from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.utils import timezone
from posts.models import SensorData
import socket
import re
import time
from dotenv import load_dotenv
import os
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)

load_dotenv()

# Reminder cooldown: avoid repeated emails for unchanged WARNING/FIRE states.
ALERT_REMINDER_COOLDOWN = getattr(settings, "ALERT_REMINDER_COOLDOWN", 1800)


def _get_alert_recipients():
    env_recipients = [r.strip() for r in settings.ALERT_EMAIL_RECIPIENTS if r.strip()]

    # Only send to users who are currently logged in (have a non-expired session).
    active_sessions = Session.objects.filter(expire_date__gte=timezone.now())
    logged_in_ids = set()
    for session in active_sessions:
        data = session.get_decoded()
        uid = data.get("_auth_user_id")
        if uid:
            logged_in_ids.add(int(uid))

    user_recipients = list(
        User.objects.filter(pk__in=logged_in_ids, is_active=True)
        .exclude(email="")
        .values_list("email", flat=True)
    )

    # Keep original casing in outgoing addresses while deduplicating case-insensitively.
    seen = set()
    merged = []
    for email in env_recipients + user_recipients:
        key = email.lower()
        if key in seen:
            continue
        seen.add(key)
        merged.append(email)
    return merged


def _should_send_alert(node_id, status, now, last_alert_status, last_alert_time):
    """
    Rules:
    - SAFE: never send.
    - First alert for a node: always send.
    - Status escalates (SAFE→WARNING, SAFE→FIRE, WARNING→FIRE): send only if
      at least ALERT_REMINDER_COOLDOWN seconds have passed since last alert.
    - Status unchanged and risky: send only after cooldown (periodic reminder).
    - Downgrade (FIRE→WARNING) or re-entry after safe: treated same as escalation.
    """
    if status not in ("WARNING", "FIRE"):
        return False

    prev_status = last_alert_status.get(node_id, "SAFE")
    last = last_alert_time.get(node_id, 0)
    elapsed = now - last

    # Always enforce minimum cooldown between any two emails for the same node.
    if elapsed < ALERT_REMINDER_COOLDOWN:
        return False

    # Past cooldown: send if risky (new escalation or persistent risk).
    return True

def send_alert_email(node_id, status, temp, smoke, hum):
    recipients = _get_alert_recipients()
    if not recipients or not settings.EMAIL_HOST_USER:
        return

    subject = f"[FIRE DETECTION] {status} Alert - Node {node_id}"
    message = (
        f"Alert Level: {status}\n"
        f"Node ID   : {node_id}\n"
        f"Temperature: {temp}°C\n"
        f"Smoke      : {smoke}\n"
        f"Humidity   : {hum}%\n\n"
        f"Please check the dashboard immediately."
    )

    for recipient in recipients:
        try:
            send_mail(subject, message, settings.EMAIL_HOST_USER, [recipient], fail_silently=False)
            logger.info("Alert email sent to %s for Node %s (%s)", recipient, node_id, status)
        except Exception as e:
            logger.error("Failed to send alert email to %s: %s", recipient, e)

class Command(BaseCommand):
    help = "Read data from Cooja Serial Socket (auto reconnect)"

    def handle(self, *args, **kwargs):
        
        HOST = os.getenv("SOCKET_HOST", "127.0.0.1")
        PORT = int(os.getenv("SOCKET_PORT", 60001))

        pattern = re.compile(
            r"node_id:(\d+),\s*T=(\d+)\s+S=(\d+)\s+H=(\d+)(?:\s+X=(\d+)\s+Y=(\d+))?"
        )

        # Track last alert state/time per node to avoid email flooding
        last_alert_time = {}
        last_alert_status = {}

        while True:
            s = None
            try:
                logger.info("Connecting to socket %s:%s ...", HOST, PORT)
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                # Keep recv timeout higher than simulation sending interval.
                s.settimeout(60)
                s.connect((HOST, PORT))
                logger.info("Connected!")

                buffer = ""

                while True:
                    data = s.recv(1024)

                    if not data:
                        raise ConnectionError("Socket closed")

                    buffer += data.decode(errors="ignore")

                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)

                        logger.debug("RAW: %s", line)  # debug

                        match = pattern.search(line)
                        if match:
                            node, temp, smoke, hum, x, y = match.groups()
                            temp = int(temp)
                            smoke = int(smoke)
                            x_value = float(x) if x is not None else None
                            y_value = float(y) if y is not None else None

                            # status logic
                            status = "SAFE"
                            if temp > 80 and smoke > 90:
                                status = "FIRE"
                            elif temp > 60 or smoke > 70:
                                status = "WARNING"

                            SensorData.objects.create(
                                node_id=int(node),
                                temperature=temp,
                                smoke=smoke,
                                humidity=int(hum),
                                status=status,
                                x=x_value,
                                y=y_value,
                            )

                            count = SensorData.objects.count()

                            if count > 1000:
                                qs = SensorData.objects.order_by('created_at')[:200]
                                ids = [obj.id for obj in qs]
                                SensorData.objects.filter(id__in=ids).delete()

                            logger.info("Saved Node %s | T=%s S=%s -> %s", node, temp, smoke, status)

                            node_key = int(node)
                            now = time.time()

                            if _should_send_alert(node_key, status, now, last_alert_status, last_alert_time):
                                last_alert_time[node_key] = now
                                send_alert_email(node_key, status, temp, smoke, int(hum))

                            # Always record latest status so next cycle can detect escalation/downgrade.
                            last_alert_status[node_key] = status

                        elif "node_id:" in line:
                            logger.warning("Unparsed sensor line: %s", line)

            except Exception as e:
                logger.error("Socket error: %s", e)
                logger.info("Reconnecting in 3 seconds...\n")
                time.sleep(3)
            finally:
                if s:
                    try:
                        s.close()
                    except OSError:
                        pass
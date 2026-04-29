from django.core.management.base import BaseCommand
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

class Command(BaseCommand):
    help = "Read data from Cooja Serial Socket (auto reconnect)"

    def handle(self, *args, **kwargs):
        
        HOST = os.getenv("SOCKET_HOST")
        PORT = int(os.getenv("SOCKET_PORT", 60001))

        pattern = re.compile(
            r"node_id:(\d+),\s*T=(\d+)\s*S=(\d+)\s*H=(\d+)"
        )

        while True:
            try:
                logger.info("Connecting to socket...")
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(10)
                s.connect((HOST, PORT))
                logger.info("Connected!")

                buffer = ""

                while True:
                    data = s.recv(1024)

                    if not data:
                        raise ConnectionError("Socket closed")

                    buffer += data.decode()

                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)

                        logger.debug("RAW: %s", line)  # debug

                        match = pattern.search(line)
                        if match:
                            node, temp, smoke, hum = match.groups()

                            temp = int(temp)
                            smoke = int(smoke)

                            # status logic
                            status = "SAFE"
                            if temp > 60 and smoke > 80:
                                status = "FIRE"
                            elif temp > 40 or smoke > 50:
                                status = "WARNING"

                            SensorData.objects.create(
                                node_id=int(node),
                                temperature=temp,
                                smoke=smoke,
                                humidity=int(hum),
                                status=status
                            )

                            count = SensorData.objects.count()

                            if count > 1000:
                                qs = SensorData.objects.order_by('created_at')[:200]
                                ids = [obj.id for obj in qs]
                                SensorData.objects.filter(id__in=ids).delete()

                            logger.info("Saved Node %s | T=%s S=%s -> %s", node, temp, smoke, status)

            except Exception as e:
                logger.error("Socket error: %s", e)
                logger.info("Reconnecting in 3 seconds...\n")
                time.sleep(3)
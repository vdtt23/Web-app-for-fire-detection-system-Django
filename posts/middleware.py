import time

from django.conf import settings
from django.contrib.auth import logout
from django.http import JsonResponse
from django.shortcuts import redirect


class IdleTimeoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.timeout = int(getattr(settings, "IDLE_TIMEOUT_SECONDS", 1800))

    def __call__(self, request):
        if request.user.is_authenticated:
            now = int(time.time())
            last_activity = request.session.get("last_activity_ts")

            if last_activity and (now - int(last_activity)) > self.timeout:
                logout(request)
                if request.path.startswith("/api/"):
                    return JsonResponse({"detail": "Session expired"}, status=401)
                return redirect("/login/?session=expired")

            # Count only real page interaction as activity; background API polling won't refresh timeout.
            if not request.path.startswith("/api/"):
                request.session["last_activity_ts"] = now

        return self.get_response(request)

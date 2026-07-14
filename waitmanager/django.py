import time
import functools
from .core import WaitManager


# Global WaitManager instance
_wm = None


def get_waitmanager():
    """Get or create the global WaitManager instance from Django settings."""
    global _wm
    from django.conf import settings
    if _wm is None:
        config = getattr(settings, "WAITMANAGER_CONFIG", {})
        _wm = WaitManager(**config)
    return _wm


class WaitManagerMiddleware:
    """Django middleware for automatic request tracking."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.wm = get_waitmanager()

    def __call__(self, request):
        if self.wm.auto_track:
            ip = self._get_ip(request)
            self.wm.track(ip=ip)

        response = self.get_response(request)
        return response

    def _get_ip(self, request):
        """Extract client IP from request."""
        x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded:
            return x_forwarded.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "unknown")


def limit(
    channel: str = "api",
    max_requests: int | None = None,
    window: float | None = None,
    block: bool = False,
):
    """Decorator to rate-limit a Django view.

    Args:
        channel: Traffic channel name.
        max_requests: Max requests in the window.
        window: Time window in seconds.
        block: If True, raise PermissionDenied instead of sleeping.

    Usage:
        @limit(channel="api")
        def my_view(request):
            return JsonResponse({"ok": True})
    """
    from django.core.exceptions import PermissionDenied
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapped(request, *args, **kwargs):
            wm = get_waitmanager()
            ip = _get_client_ip(request)

            # Custom limits
            old_low = wm.low_traffic
            old_window = wm.time_window
            if max_requests is not None:
                wm.low_traffic = max_requests
                wm.medium_traffic = max_requests * 2
            if window is not None:
                wm.time_window = window

            wait = wm.get_wait(channel=channel, ip=ip)

            # Restore
            if max_requests is not None:
                wm.low_traffic = old_low
                wm.medium_traffic = old_low * 2
            if window is not None:
                wm.time_window = old_window

            if wait > 0:
                if block:
                    raise PermissionDenied("Rate limit exceeded")
                time.sleep(wait)

            wm.add_traffic(channel=channel, ip=ip)
            return view_func(request, *args, **kwargs)
        return wrapped
    return decorator


def _get_client_ip(request):
    """Extract client IP from Django request."""
    x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded:
        return x_forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")

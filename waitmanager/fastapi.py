import time
from .core import WaitManager


class RateLimiter:
    """FastAPI dependency for rate limiting with WaitManager."""

    def __init__(self, wm: WaitManager):
        self.wm = wm

    def limit(
        self,
        channel: str = "api",
        max_requests: int | None = None,
        window: float | None = None,
    ):
        """Create a FastAPI dependency for rate limiting.

        Usage:
            limiter = RateLimiter(wm)

            @app.get("/api")
            async def api(_=Depends(limiter.limit("api"))):
                return {"ok": True}
        """
        from fastapi import Request
        async def dependency(request: Request):
            # Get client IP
            ip = request.client.host if request.client else "unknown"

            # Custom or default limits
            old_low = self.wm.low_traffic
            old_window = self.wm.time_window
            if max_requests is not None:
                self.wm.low_traffic = max_requests
                self.wm.medium_traffic = max_requests * 2
            if window is not None:
                self.wm.time_window = window

            # Calculate wait
            wait = self.wm.get_wait(channel=channel, ip=ip)

            # Restore original limits
            if max_requests is not None:
                self.wm.low_traffic = old_low
                self.wm.medium_traffic = old_low * 2
            if window is not None:
                self.wm.time_window = old_window

            # Apply wait
            if wait > 0:
                time.sleep(wait)

            # Track
            self.wm.add_traffic(channel=channel, ip=ip)

            return True

        return dependency

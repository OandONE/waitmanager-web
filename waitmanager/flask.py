import time
import functools
from .core import WaitManager


class FlaskWaitManager(WaitManager):
    """WaitManager extension for Flask with auto-tracking support."""

    def init_app(
        self,
        app
    ):
        """Initialize WaitManager with Flask app.

        Usage:
            wm = FlaskWaitManager()
            wm.init_app(app)
        """
        if not hasattr(app, 'extensions'):
            app.extensions = {}
        app.extensions['waitmanager'] = self

    def limit(
        self,
        channel: str = "api",
        max_requests: int | None = None,
        window: float| None = None,
    ):
        """Decorator to rate-limit a Flask route.

        Args:
            channel: Traffic channel name.
            max_requests: Max requests in the window.
            window: Time window in seconds.
        """
        from flask import request
        def decorator(f):
            @functools.wraps(f)
            def wrapped(*args, **kwargs):
                # Get client IP
                ip = request.remote_addr

                # Custom or default limits
                old_low = self.low_traffic
                old_window = self.time_window
                if max_requests is not None:
                    self.low_traffic = max_requests
                    self.medium_traffic = max_requests * 2
                if window is not None:
                    self.time_window = window

                # Calculate wait
                wait = self.get_wait(channel=channel, ip=ip)

                # Restore original limits
                if max_requests is not None:
                    self.low_traffic = old_low
                    self.medium_traffic = old_low * 2
                if window is not None:
                    self.time_window = old_window

                if wait > 0:
                    time.sleep(wait)

                # Track
                self.add_traffic(channel=channel, ip=ip)

                return f(*args, **kwargs)
            return wrapped
        return decorator

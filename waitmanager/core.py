import time
import threading
from typing import Optional, Callable


class WaitManager:
    """Intelligent Rate Limiting with separate traffic channels."""

    def __init__(
        self,
        low_traffic: int = 100,
        medium_traffic: int = 200,
        low_wait: float = 0.0,
        medium_wait: float = 0.5,
        high_wait: float = 2.0,
        time_window: float = 60.0,
        auto_track: bool = False,
        per_ip: bool = True,
        sleep_callback: Optional[Callable] = None,
        channels: Optional[list] = None,
    ):
        self.low_traffic = low_traffic
        self.medium_traffic = medium_traffic
        self.low_wait = low_wait
        self.medium_wait = medium_wait
        self.high_wait = high_wait
        self.time_window = time_window
        self.auto_track = auto_track
        self.per_ip = per_ip
        self.sleep_callback = sleep_callback

        default_channels = ["api", "login", "upload", "download", "search", "signup"]
        self._channels = channels or default_channels
        self._traffic: dict[str, dict[str, list[float]]] = {
            ch: {} for ch in self._channels
        }
        self._lock = threading.Lock()

    def add_traffic(
        self,
        count: int = 1,
        channel: str = "api",
        ip: Optional[str] = None,
    ):
        """Register traffic in a specific channel."""
        if channel not in self._traffic:
            raise ValueError(f"Invalid channel: {channel}")

        key = ip if (self.per_ip and ip) else "_global"
        now = time.time()

        with self._lock:
            if key not in self._traffic[channel]:
                self._traffic[channel][key] = []

            for _ in range(count):
                self._traffic[channel][key].append(now)

        self._clean_old(channel, key)

    def track(self, ip: Optional[str] = None):
        """Auto-track a request."""
        self.add_traffic(ip=ip)

    def _clean_old(self, channel: str, key: str = "_global"):
        """Remove expired traffic entries."""
        cutoff = time.time() - self.time_window
        with self._lock:
            if key in self._traffic[channel]:
                self._traffic[channel][key] = [
                    t for t in self._traffic[channel][key] if t > cutoff
                ]

    def get_wait(self, channel: str = "api", ip: Optional[str] = None) -> float:
        """Calculate wait time for a channel and IP."""
        if channel not in self._traffic:
            return 0.0

        key = ip if (self.per_ip and ip) else "_global"
        self._clean_old(channel, key)

        with self._lock:
            count = len(self._traffic[channel].get(key, []))

        if self.sleep_callback:
            try:
                result = self.sleep_callback(
                    channel=channel,
                    messages_count=count,
                )
                if isinstance(result, (int, float)):
                    return float(result)
            except Exception:
                pass

        if count <= self.low_traffic:
            return self.low_wait
        elif count <= self.medium_traffic:
            return self.medium_wait
        else:
            return self.high_wait

    def reset(self, channel: Optional[str] = None, ip: Optional[str] = None):
        """Reset traffic."""
        with self._lock:
            if channel and ip:
                self._traffic[channel].pop(ip, None)
            elif channel:
                self._traffic[channel].clear()
            else:
                for ch in self._traffic:
                    self._traffic[ch].clear()

    @property
    def count(self) -> int:
        return len(self._channels)

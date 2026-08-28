import time

HOUR_SECONDS = 3600
DAY_SECONDS = 86400


class RateLimiter:
    """In-memory sliding-window limiter: `per_ip_per_hour` requests per IP,
    plus a `daily_cap` shared across every IP. Both windows must have room
    for a request to be allowed.
    """
    def __init__(self, per_ip_per_hour: int, daily_cap: int, now=time.time):
        self.per_ip_per_hour = per_ip_per_hour
        self.daily_cap = daily_cap
        self._now = now
        self._ip_hits: dict[str, list[float]] = {}
        self._daily_hits: list[float] = []

    def allow(self, ip: str) -> bool:
        now = self._now()
        ip_hits = [t for t in self._ip_hits.get(ip, []) if now - t < HOUR_SECONDS]
        daily_hits = [t for t in self._daily_hits if now - t < DAY_SECONDS]

        if len(ip_hits) >= self.per_ip_per_hour or len(daily_hits) >= self.daily_cap:
            self._ip_hits[ip] = ip_hits
            self._daily_hits = daily_hits
            return False

        ip_hits.append(now)
        daily_hits.append(now)
        self._ip_hits[ip] = ip_hits
        self._daily_hits = daily_hits
        return True

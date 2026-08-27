from api.ratelimit import RateLimiter


def test_allows_requests_under_the_per_ip_limit():
    limiter = RateLimiter(per_ip_per_hour=3, daily_cap=100)
    assert limiter.allow("1.2.3.4") is True
    assert limiter.allow("1.2.3.4") is True
    assert limiter.allow("1.2.3.4") is True


def test_blocks_the_same_ip_once_it_exceeds_the_per_ip_limit():
    limiter = RateLimiter(per_ip_per_hour=2, daily_cap=100)
    limiter.allow("1.2.3.4")
    limiter.allow("1.2.3.4")
    assert limiter.allow("1.2.3.4") is False


def test_per_ip_limit_does_not_affect_other_ips():
    limiter = RateLimiter(per_ip_per_hour=1, daily_cap=100)
    limiter.allow("1.2.3.4")
    assert limiter.allow("5.6.7.8") is True


def test_blocks_every_ip_once_the_daily_cap_is_hit():
    limiter = RateLimiter(per_ip_per_hour=100, daily_cap=2)
    limiter.allow("1.2.3.4")
    limiter.allow("5.6.7.8")
    assert limiter.allow("9.9.9.9") is False


def test_per_ip_window_expires_after_an_hour():
    clock = [0.0]
    limiter = RateLimiter(per_ip_per_hour=1, daily_cap=100, now=lambda: clock[0])

    assert limiter.allow("1.2.3.4") is True
    assert limiter.allow("1.2.3.4") is False

    clock[0] += 3601
    assert limiter.allow("1.2.3.4") is True


def test_daily_cap_expires_after_a_day():
    clock = [0.0]
    limiter = RateLimiter(per_ip_per_hour=100, daily_cap=1, now=lambda: clock[0])

    assert limiter.allow("1.2.3.4") is True
    assert limiter.allow("5.6.7.8") is False

    clock[0] += 86401
    assert limiter.allow("5.6.7.8") is True

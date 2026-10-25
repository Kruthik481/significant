from app.limits import RateLimiter


def test_allows_up_to_the_limit_then_reports_retry_after():
    t = [1000.0]
    lim = RateLimiter(2, window=3600, now=lambda: t[0])
    assert lim.allow("ip")[0]
    t[0] += 10
    assert lim.allow("ip")[0]
    ok, retry = lim.allow("ip")
    assert not ok and retry == 3590
    assert lim.allow("other")[0]


def test_window_slides_and_empty_keys_are_dropped():
    t = [0.0]
    lim = RateLimiter(1, window=60, now=lambda: t[0])
    assert lim.allow("ip")[0]
    t[0] = 61
    assert lim.allow("ip")[0]
    t[0] = 200
    lim.allow("x")
    assert "ip" not in lim._log

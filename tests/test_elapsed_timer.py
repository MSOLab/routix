import time
from datetime import datetime

from routix import ElapsedTimer


def test_elapsed_timer_initialization():
    timer = ElapsedTimer()
    now = datetime.now()
    # Should be very close to now
    assert abs((timer.start_dt - now).total_seconds()) < 0.1


def test_elapsed_and_remaining():
    timer = ElapsedTimer()
    time.sleep(0.05)
    elapsed = timer.get_elapsed_sec()
    # elapsed should be around 0.05, allow a bit more for slow machines
    assert 0.03 < elapsed < 0.2

    # Remaining time (total 1 second) should be slightly less than 1
    remaining = timer.get_remaining_sec(1)
    assert 0.7 < remaining < 1.0


def test_time_over_and_reset():
    timer = ElapsedTimer()
    time.sleep(0.02)
    assert not timer.time_over(0.1)
    time.sleep(0.15)
    assert timer.time_over(0.1)

    # After reset, time_over should be False again
    timer.reset()
    assert not timer.time_over(0.1)


def test_str_and_formatting():
    timer = ElapsedTimer()
    s = str(timer)
    assert "ElapsedTimer started @" in s

    iso_str = timer.get_start_dt_isoformatted()
    assert "T" in iso_str
    strf_str = timer.get_start_dt_strftime()
    assert "T" in strf_str


def test_negative_remaining_is_zero():
    timer = ElapsedTimer()
    assert timer.get_remaining_sec(0) == 0.0
    time.sleep(0.02)
    assert timer.get_remaining_sec(0) == 0.0

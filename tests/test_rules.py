"""Rule gate: fast unit tests on the domain, each linked to the AC it proves."""
from datetime import date, datetime, timedelta, timezone

import pytest

from booking.clock import FixedClock
from booking.domain import BookingService, DomainError
from booking.repository import InMemoryRepository

NOW = datetime(2026, 10, 1, 9, 0, tzinfo=timezone.utc)


@pytest.fixture
def service():
    clock = FixedClock(NOW)
    return BookingService(InMemoryRepository.seeded(clock.now()), clock)


def _code(fn) -> str:
    with pytest.raises(DomainError) as err:
        fn()
    return err.value.code


@pytest.mark.ac("AC-001")
def test_booking_marks_slot_taken(service):
    appt = service.book("P-100", "PR-001-D1-0930")
    assert appt.status == "BOOKED"
    assert "PR-001-D1-0930" not in [s.id for s in service.open_slots("PR-001", date(2026, 10, 2))]


@pytest.mark.ac("AC-002")
def test_no_double_booking(service):
    service.book("P-100", "PR-001-D1-1100")
    assert _code(lambda: service.book("P-101", "PR-001-D1-1100")) == "SLOT_UNAVAILABLE"


@pytest.mark.ac("AC-003")
def test_slot_starting_exactly_now_is_in_the_past():
    """Boundary case for BR-2: 'at or before the current time'."""
    clock = FixedClock(datetime(2026, 10, 1, 9, 30, tzinfo=timezone.utc))
    svc = BookingService(InMemoryRepository.seeded(clock.now()), clock)
    assert _code(lambda: svc.book("P-100", "PR-001-D0-0930")) == "SLOT_IN_PAST"


@pytest.mark.ac("AC-005")
def test_cancelled_appointments_do_not_count_towards_limit(service):
    a = service.book("P-200", "PR-002-D2-0930")
    service.book("P-200", "PR-002-D2-1100")
    service.book("P-200", "PR-002-D2-1400")
    service.cancel(a.id)
    assert service.book("P-200", "PR-002-D2-1600").status == "BOOKED"


@pytest.mark.ac("AC-006")
def test_cancel_exactly_24h_before_is_allowed():
    """Boundary case for BR-4: '24 hours or more'."""
    clock = FixedClock(datetime(2026, 10, 1, 9, 30, tzinfo=timezone.utc))
    svc = BookingService(InMemoryRepository.seeded(clock.now()), clock)
    appt = svc.book("P-100", "PR-001-D1-0930")
    assert appt.start - clock.now() == timedelta(hours=24)
    assert svc.cancel(appt.id).status == "CANCELLED"


@pytest.mark.ac("AC-007")
def test_cancel_one_minute_inside_window_is_rejected():
    clock = FixedClock(datetime(2026, 10, 1, 9, 31, tzinfo=timezone.utc))
    svc = BookingService(InMemoryRepository.seeded(clock.now()), clock)
    appt = svc.book("P-100", "PR-001-D1-0930")
    assert _code(lambda: svc.cancel(appt.id)) == "CANCELLATION_WINDOW_CLOSED"


@pytest.mark.ac("AC-008")
def test_open_slots_are_sorted_and_future_only(service):
    slots = service.open_slots("PR-001", date(2026, 10, 1))
    assert [s.start for s in slots] == sorted(s.start for s in slots)
    assert all(s.start > NOW for s in slots)

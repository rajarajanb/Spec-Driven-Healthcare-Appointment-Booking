"""Business rules from spec.md (BR-1..BR-6). No web framework imports here."""
from __future__ import annotations

import itertools
from datetime import date, timedelta

from .clock import Clock
from .repository import Appointment, InMemoryRepository, Slot

MAX_ACTIVE_APPOINTMENTS = 3            # BR-3
CANCELLATION_WINDOW = timedelta(hours=24)  # BR-4


class DomainError(Exception):
    """A rule violation. `code` values are the exact strings in spec.md and openapi.yaml."""

    def __init__(self, code: str, status: int, message: str) -> None:
        super().__init__(message)
        self.code, self.status, self.message = code, status, message


class BookingService:
    def __init__(self, repo: InMemoryRepository, clock: Clock) -> None:
        self.repo, self.clock = repo, clock
        self._ids = itertools.count(1)

    # US-1 / AC-008
    def open_slots(self, provider_id: str, on: date) -> list[Slot]:
        if provider_id not in self.repo.providers:
            raise DomainError("PROVIDER_NOT_FOUND", 404, f"Provider {provider_id} not found")
        now = self.clock.now()
        slots = [
            s for s in self.repo.slots.values()
            if s.provider_id == provider_id
            and s.start.date() == on
            and s.start > now                                   # BR-2
            and self.repo.active_appointment_for_slot(s.id) is None  # BR-1
        ]
        return sorted(slots, key=lambda s: s.start)

    # US-2 / AC-001..AC-005
    def book(self, patient_id: str, slot_id: str) -> Appointment:
        slot = self.repo.slots.get(slot_id)
        if slot is None:
            raise DomainError("SLOT_NOT_FOUND", 404, f"Slot {slot_id} not found")
        now = self.clock.now()
        if slot.start <= now:  # BR-2
            raise DomainError("SLOT_IN_PAST", 422, "This slot has already started")
        if self.repo.active_appointment_for_slot(slot_id):  # BR-1
            raise DomainError("SLOT_UNAVAILABLE", 409, "This slot is already booked")
        active = [
            a for a in self.repo.appointments.values()
            if a.patient_id == patient_id and a.status == "BOOKED" and a.start > now
        ]
        if len(active) >= MAX_ACTIVE_APPOINTMENTS:  # BR-3
            raise DomainError(
                "BOOKING_LIMIT_REACHED", 409,
                f"Patients may hold at most {MAX_ACTIVE_APPOINTMENTS} upcoming appointments",
            )
        appt = Appointment(f"APT-{next(self._ids):05d}", patient_id, slot.provider_id, slot.id, slot.start)
        self.repo.appointments[appt.id] = appt
        return appt

    def get(self, appointment_id: str) -> Appointment:
        appt = self.repo.appointments.get(appointment_id)
        if appt is None:
            raise DomainError("APPOINTMENT_NOT_FOUND", 404, f"Appointment {appointment_id} not found")
        return appt

    # US-3 / AC-006, AC-007
    def cancel(self, appointment_id: str) -> Appointment:
        appt = self.get(appointment_id)
        if appt.status == "CANCELLED":  # BR-6
            return appt
        if appt.start - self.clock.now() < CANCELLATION_WINDOW:  # BR-4
            raise DomainError(
                "CANCELLATION_WINDOW_CLOSED", 409,
                "Appointments can only be cancelled 24 hours or more in advance",
            )
        appt.status = "CANCELLED"  # BR-5: slot is free because it has no BOOKED appointment
        return appt

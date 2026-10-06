"""In-memory storage and seed data (plan.md: Storage, Seed data)."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, time, timedelta

PROVIDERS = {
    "PR-001": "Dr. Sivaji (Cardiology)",
    "PR-002": "Dr. Vikram (Dermatology)",
}
SLOT_TIMES = [time(8, 0), time(9, 30), time(11, 0), time(14, 0), time(16, 0)]
SLOT_MINUTES = 30
SEED_DAYS = 4  # today + 3 days


@dataclass(frozen=True)
class Slot:
    id: str
    provider_id: str
    start: datetime
    end: datetime


@dataclass
class Appointment:
    id: str
    patient_id: str
    provider_id: str
    slot_id: str
    start: datetime
    status: str = "BOOKED"


@dataclass
class InMemoryRepository:
    providers: dict[str, str] = field(default_factory=dict)
    slots: dict[str, Slot] = field(default_factory=dict)
    appointments: dict[str, Appointment] = field(default_factory=dict)

    @classmethod
    def seeded(cls, today: datetime) -> "InMemoryRepository":
        """Create slots relative to `today` so IDs like PR-001-D1-0930 are stable in every run."""
        repo = cls(providers=dict(PROVIDERS))
        day0 = today.replace(hour=0, minute=0, second=0, microsecond=0)
        for provider_id in PROVIDERS:
            for d in range(SEED_DAYS):
                for t in SLOT_TIMES:
                    start = day0 + timedelta(days=d, hours=t.hour, minutes=t.minute)
                    slot_id = f"{provider_id}-D{d}-{t.hour:02d}{t.minute:02d}"
                    repo.slots[slot_id] = Slot(slot_id, provider_id, start, start + timedelta(minutes=SLOT_MINUTES))
        return repo

    def active_appointment_for_slot(self, slot_id: str) -> Appointment | None:
        return next(
            (a for a in self.appointments.values() if a.slot_id == slot_id and a.status == "BOOKED"),
            None,
        )

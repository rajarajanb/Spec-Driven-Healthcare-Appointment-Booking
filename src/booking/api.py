"""HTTP layer. Shapes here mirror contracts/openapi.yaml; the contract tests keep them honest."""
from __future__ import annotations

from datetime import date, datetime, timezone

from fastapi import FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from .clock import Clock, SystemClock
from .domain import BookingService, DomainError
from .repository import Appointment, InMemoryRepository, Slot


class BookingRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    patientId: str = Field(pattern=r"^P-[0-9]{3,}$")
    slotId: str = Field(min_length=1)


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _slot(s: Slot) -> dict:
    return {"id": s.id, "providerId": s.provider_id, "start": _iso(s.start), "end": _iso(s.end)}


def _appt(a: Appointment) -> dict:
    return {
        "id": a.id, "patientId": a.patient_id, "providerId": a.provider_id,
        "slotId": a.slot_id, "start": _iso(a.start), "status": a.status,
    }


def create_app(clock: Clock | None = None) -> FastAPI:
    clock = clock or SystemClock()
    service = BookingService(InMemoryRepository.seeded(clock.now()), clock)
    app = FastAPI(title="Provider Appointment Booking API", version="1.0.0")
    app.state.service = service

    # NFR-2: one error envelope for everything
    @app.exception_handler(DomainError)
    async def _domain_error(_: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse({"code": exc.code, "message": exc.message}, status_code=exc.status)

    @app.exception_handler(RequestValidationError)
    async def _validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        first = exc.errors()[0] if exc.errors() else {}
        where = ".".join(str(p) for p in first.get("loc", []))
        return JSONResponse(
            {"code": "VALIDATION_ERROR", "message": f"{where}: {first.get('msg', 'invalid request')}"},
            status_code=422,
        )

    @app.get("/health")
    def get_health() -> dict:
        return {"status": "ok"}

    @app.get("/providers/{providerId}/slots")
    def list_open_slots(providerId: str, date_: date = Query(alias="date")) -> dict:
        slots = service.open_slots(providerId, date_)
        return {"providerId": providerId, "date": date_.isoformat(), "slots": [_slot(s) for s in slots]}

    @app.post("/appointments", status_code=201)
    def book_appointment(req: BookingRequest) -> dict:
        return _appt(service.book(req.patientId, req.slotId))

    @app.get("/appointments/{appointmentId}")
    def get_appointment(appointmentId: str) -> dict:
        return _appt(service.get(appointmentId))

    @app.post("/appointments/{appointmentId}/cancel")
    def cancel_appointment(appointmentId: str) -> dict:
        return _appt(service.cancel(appointmentId))

    return app

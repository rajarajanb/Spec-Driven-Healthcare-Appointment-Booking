# Spec 001 — Provider Appointment Booking

> **Status:** Approved · **Owner:** Product + Engineering · **Version:** 1.0.0
>
> This file describes **what** the system must do and **why**. It says nothing about
> frameworks, databases or code structure — that belongs in `plan.md`.
> Every acceptance criterion has a stable ID (`AC-xxx`). Tests must reference these IDs;
> `tools/check_traceability.py` fails the build if any criterion is untested.

## 1. Problem

Patients who find a provider (see the Healthcare NLP Provider Search project) still have to
phone the clinic to book. Front-desk staff juggle double bookings and late cancellations.
We need a small, reliable booking API that clinics and patient apps can integrate with.

## 2. Users

| Actor | Goal |
|---|---|
| Patient (via app) | See open slots, book one, cancel if plans change |
| Clinic front desk | Trust that a slot is never double-booked |
| Clinic operations | Protect provider time from last-minute cancellations |

## 3. User stories

- **US-1** As a patient, I want to see a provider's open slots for a day, so I can pick a time.
- **US-2** As a patient, I want to book a slot, so my visit is confirmed without a phone call.
- **US-3** As a patient, I want to cancel a booking, so the slot is freed for someone else.
- **US-4** As a clinic, I want booking rules enforced by the system, not by staff memory.

## 4. Business rules

- **BR-1** A slot can hold at most one active (BOOKED) appointment.
- **BR-2** Slots that start at or before the current time cannot be booked.
- **BR-3** A patient may hold at most **5** active upcoming appointments.
- **BR-4** A patient may cancel only when the appointment starts **24 hours or more** from now.
- **BR-5** A cancelled appointment frees its slot immediately.
- **BR-6** Cancelling an already-cancelled appointment is idempotent: it returns the appointment unchanged.

## 5. Acceptance criteria

Written as Given / When / Then. Executable versions live in `acceptance.yaml`.

- **AC-001** (US-2) Given an open future slot, when a patient books it, then the API returns
  `201` with status `BOOKED`, and the slot no longer appears in the open-slot list.
- **AC-002** (US-2, BR-1) Given a slot that is already booked, when another patient books it,
  then the API returns `409` with code `SLOT_UNAVAILABLE`.
- **AC-003** (US-2, BR-2) Given a slot that has already started, when a patient books it,
  then the API returns `422` with code `SLOT_IN_PAST`.
- **AC-004** (US-2) Given a slot ID that does not exist, when a patient books it,
  then the API returns `404` with code `SLOT_NOT_FOUND`.
- **AC-005** (US-4, BR-3) Given a patient with 5 active upcoming appointments, when they book
  a 6th, then the API returns `409` with code `BOOKING_LIMIT_REACHED`.
- **AC-006** (US-3, BR-4, BR-5, BR-6) Given a booking that starts 24h or more from now, when the
  patient cancels, then the API returns `200` with status `CANCELLED` and the slot is open again.
  Cancelling it a second time returns `200` with the same appointment (BR-6).
- **AC-007** (US-3, BR-4) Given a booking that starts in less than 24h, when the patient
  cancels, then the API returns `409` with code `CANCELLATION_WINDOW_CLOSED`.
- **AC-008** (US-1) Given a provider and a date, when a patient lists slots, then only open,
  future slots for that provider and date are returned, ordered by start time.
- **AC-009** (US-2) Given a malformed request (e.g. bad patient ID), when it is sent, then the
  API returns `422` with code `VALIDATION_ERROR` in the standard error envelope.
- **AC-010** (US-1, US-3) Given an unknown appointment ID or provider ID, when it is used, then
  the API returns `404` with code `APPOINTMENT_NOT_FOUND` or `PROVIDER_NOT_FOUND`.

## 6. Non-functional requirements

- **NFR-1** Every response body — success or error — must conform to `contracts/openapi.yaml`.
  No undocumented fields, no undocumented status codes.
- **NFR-2** Errors use one envelope: `{ "code": "<MACHINE_CODE>", "message": "<human text>" }`.
- **NFR-3** Business rules must be testable with a controllable clock (no `sleep`, no real time).

## 7. Out of scope (v1)

Authentication, payments, reminders, rescheduling, provider calendars management, persistence
beyond process memory. Each is a candidate for a future spec (`002-…`).

## 8. Open questions

- None blocking v1. (Rescheduling is tracked as a separate spec.)

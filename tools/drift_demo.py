#!/usr/bin/env python3
"""Show that the gates catch spec drift.

Copies the repo to a temp folder, applies one "innocent-looking" change at a time,
runs the gates, and reports whether the drift was caught. Your working copy is never touched.

Usage:  python tools/drift_demo.py
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DRIFTS = [
    (
        "Developer adds an extra 'notes' field to the Appointment response",
        "src/booking/api.py",
        '"status": a.status,\n    }',
        '"status": a.status, "notes": "",\n    }',
    ),
    (
        "Developer returns 400 instead of 409 for a double booking",
        "src/booking/domain.py",
        '"SLOT_UNAVAILABLE", 409',
        '"SLOT_UNAVAILABLE", 400',
    ),
    (
        "Developer quietly raises the booking limit from 3 to 5",
        "src/booking/domain.py",
        "MAX_ACTIVE_APPOINTMENTS = 3",
        "MAX_ACTIVE_APPOINTMENTS = 5",
    ),
    (
        "Developer adds a DELETE endpoint that is not in the contract",
        "src/booking/api.py",
        "    return app\n",
        '    @app.delete("/appointments/{appointmentId}")\n'
        "    def delete_appointment(appointmentId: str) -> dict:\n"
        "        return {}\n\n    return app\n",
    ),
    (
        "Product adds AC-011 to spec.md but nobody writes a test for it",
        "specs/001-appointment-booking/spec.md",
        "## 6. Non-functional requirements",
        "- **AC-011** (US-3) Given a booking, when the patient reschedules it, then the old slot is freed.\n\n"
        "## 6. Non-functional requirements",
    ),
]


def run_gates(cwd: Path) -> tuple[bool, str]:
    tests = subprocess.run([sys.executable, "-m", "pytest", "-q", "-x", "--no-header", "-p", "no:cacheprovider"],
                           cwd=cwd, capture_output=True, text=True)
    trace = subprocess.run([sys.executable, "tools/check_traceability.py"], cwd=cwd, capture_output=True, text=True)
    out = tests.stdout + trace.stdout
    reason = next((l.strip() for l in out.splitlines() if l.strip().startswith(("E  ", "FAIL:"))), "")
    return tests.returncode == 0 and trace.returncode == 0, reason[:160]


def main() -> int:
    caught = 0
    for title, rel, old, new in DRIFTS:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / "repo"
            shutil.copytree(ROOT, work, ignore=shutil.ignore_patterns(".git", ".venv", "__pycache__", ".pytest_cache"))
            target = work / rel
            text = target.read_text()
            assert old in text, f"demo patch no longer applies to {rel}"
            target.write_text(text.replace(old, new, 1))
            passed, reason = run_gates(work)
        status = "NOT CAUGHT" if passed else "CAUGHT"
        caught += not passed
        print(f"[{status:>10}] {title}\n             {reason}\n")
    print(f"{caught}/{len(DRIFTS)} drifts caught by the spec gates")
    return 0 if caught == len(DRIFTS) else 1


if __name__ == "__main__":
    raise SystemExit(main())

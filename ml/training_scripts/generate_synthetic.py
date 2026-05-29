"""Generate a synthetic students dataset with realistic distributions.

Usage:
    python ml/training_scripts/generate_synthetic.py --rows 1000 --out datasets/synthetic_students.csv
"""

from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path


DEPARTMENTS = ["CSE", "IT", "ECE", "MECH", "CIVIL", "MBA"]
GENDERS = ["M", "F"]

FIRST = [
    "Aarav", "Ananya", "Rahul", "Riya", "Vikram", "Priya", "Karan", "Neha", "Arjun", "Pooja",
    "Sahil", "Sneha", "Aman", "Isha", "Rohan", "Tara", "Manoj", "Kiran", "Ravi", "Simran",
    "Ali", "Maya", "Dev", "Asha", "Sara", "Imran", "Lina", "Aditya", "Megha", "Nikhil",
]
LAST = [
    "Sharma", "Verma", "Patel", "Khan", "Iyer", "Rao", "Singh", "Reddy", "Das", "Bose",
    "Kapoor", "Joshi", "Mehta", "Pillai", "Nair", "Shah", "Gupta", "Banerjee", "Mukherjee", "Pawar",
]


def label_for(row: dict) -> str:
    a = row["attendance_pct"]
    b = row["backlogs"]
    i = row["internal_marks"]
    f = row["fee_delay_days"]
    if a < 60 or b >= 3 or i < 40:
        return "high"
    if a < 75 or b >= 1 or i < 55 or f > 30:
        return "medium"
    return "low"


def make_row(rng: random.Random, idx: int) -> dict:
    dept = rng.choice(DEPARTMENTS)
    gender = rng.choice(GENDERS)
    age = rng.randint(17, 25)
    semester = rng.randint(1, 8)

    # Three realistic personas: thriving, average, struggling.
    persona = rng.choices(["thriving", "average", "struggling"], weights=[0.35, 0.45, 0.20])[0]
    if persona == "thriving":
        attendance = rng.uniform(82, 98)
        internal = rng.uniform(70, 95)
        sem_marks = rng.uniform(70, 92)
        backlogs = 0
        fee_delay = 0
        financial = rng.choice(["medium", "high"])
        placement = rng.choice(["medium", "high", "high"])
    elif persona == "average":
        attendance = rng.uniform(70, 88)
        internal = rng.uniform(50, 75)
        sem_marks = rng.uniform(50, 75)
        backlogs = rng.choice([0, 0, 1])
        fee_delay = rng.choice([0, 0, rng.randint(0, 30)])
        financial = rng.choice(["low", "medium", "medium"])
        placement = rng.choice(["low", "medium", "medium"])
    else:
        attendance = rng.uniform(38, 70)
        internal = rng.uniform(20, 55)
        sem_marks = rng.uniform(25, 55)
        backlogs = rng.randint(1, 6)
        fee_delay = rng.randint(20, 180)
        financial = rng.choice(["low", "low", "medium"])
        placement = rng.choice(["low", "low", "medium"])

    fee_paid = fee_delay <= 7
    extracurricular = rng.choice(
        ["", "music", "robotics club", "football, debate", "sports", "literary club", ""]
    )
    behavioral = rng.choice(["", "", "calm", "warning: late submissions", "discipline: clean"])
    family_bg = rng.choice(["stable", "single parent", "joint family", "", "support: high"])
    counselor = ""

    name = f"{rng.choice(FIRST)} {rng.choice(LAST)}"
    roll_no = f"{dept}{semester:02d}{idx:04d}"

    row = {
        "roll_no": roll_no,
        "name": name,
        "age": age,
        "gender": gender,
        "department_code": dept,
        "semester": semester,
        "attendance_pct": round(attendance, 2),
        "internal_marks": round(internal, 1),
        "semester_marks": round(sem_marks, 1),
        "backlogs": backlogs,
        "fee_paid": "true" if fee_paid else "false",
        "fee_delay_days": fee_delay,
        "financial_status": financial,
        "family_background": family_bg,
        "behavioral_indicators": behavioral,
        "extracurricular": extracurricular,
        "placement_readiness": placement,
        "counselor_remarks": counselor,
    }
    row["risk_level"] = label_for(row)
    # 10% label noise so the model has something to learn.
    if rng.random() < 0.10:
        choices = [r for r in ("low", "medium", "high") if r != row["risk_level"]]
        row["risk_level"] = rng.choice(choices)
    return row


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a synthetic students dataset.")
    parser.add_argument("--rows", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "datasets" / "synthetic_students.csv",
    )
    args = parser.parse_args()

    rng = random.Random(args.seed)
    args.out.parent.mkdir(parents=True, exist_ok=True)

    fields = list(make_row(rng, 0).keys())
    with args.out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for i in range(args.rows):
            w.writerow(make_row(rng, i + 1))
    print(f"✔ wrote {args.rows} rows → {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

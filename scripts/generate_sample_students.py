"""Generate datasets/sample_students.csv with 15 students per degree program."""

from __future__ import annotations

import csv
import random
from pathlib import Path

DEPARTMENTS: list[tuple[str, str]] = [
    ("Bachelor of Arts in History, Economics and Political Science", "BA-HEP"),
    ("Bachelor of Arts in Criminology, Psychology and Journalism", "BA-CPJ"),
    ("Bachelor of Commerce", "BCOM"),
    ("Bachelor of Commerce in Logistics and Supply Chain Management", "BCOM-LSCM"),
    ("Bachelor of Science in Electronics, Mathematics and Computer Science", "BSC-EMCS"),
    ("Bachelor of Science in Chemistry, Biotechnology and Life Sciences", "BSC-CBLS"),
    ("Bachelor of Science in Psychology, Chemistry and Mathematics", "BSC-PCMATH"),
    ("Bachelor of Science in Physics, Mathematics and Computer Science", "BSC-PMCS"),
    ("Bachelor of Science in Physics, Chemistry and Mathematics", "BSC-PCM"),
    ("Bachelor of Science in Clinical Nutrition and Dietetics", "BSC-CND"),
    ("Bachelor of Science in Forensic Science", "BSC-FS"),
    ("Bachelor of Social Work", "BSW"),
    ("Bachelor of Business Administration", "BBA"),
    ("Bachelor of Business Administration in Aviation Management", "BBA-AM"),
    ("Bachelor of Computer Applications", "BCA"),
    ("Bachelor of Hotel Management", "BHM"),
    ("Bachelor of Tourism and Travel Management", "BTTM"),
    ("Master of Tourism and Travel Management", "MTTM"),
    ("Master of Commerce", "MCOM"),
    ("Master of Arts in Economics", "MA-ECO"),
    ("Master of Arts in Kannada", "MA-KAN"),
    ("Master of Arts in English", "MA-ENG"),
    ("Master of Science in Computer Science", "MSC-CS"),
    ("Master of Science in Organic Chemistry", "MSC-OC"),
    ("Master of Science in Inorganic Chemistry", "MSC-IC"),
    ("Master of Science in Physical Chemistry", "MSC-PC"),
    ("Master of Science in Botany", "MSC-BOT"),
    ("Master of Social Work", "MSW"),
    ("Master of Business Administration", "MBA"),
    ("Master of Computer Applications", "MCA"),
]

GENDERS = ["M", "F"]
FIRST = [
    "Aarav", "Ananya", "Rahul", "Riya", "Vikram", "Priya", "Karan", "Neha", "Arjun", "Pooja",
    "Sahil", "Sneha", "Aman", "Isha", "Rohan", "Tara", "Manoj", "Kiran", "Ravi", "Simran",
    "Ali", "Maya", "Dev", "Asha", "Sara", "Imran", "Lina", "Aditya", "Megha", "Nikhil",
    "Divya", "Harish", "Kavya", "Sanjay", "Anjali", "Vivek", "Pooja", "Yash", "Naina", "Rohit",
]
LAST = [
    "Sharma", "Verma", "Patel", "Khan", "Iyer", "Rao", "Singh", "Reddy", "Das", "Bose",
    "Kapoor", "Joshi", "Mehta", "Pillai", "Nair", "Shah", "Gupta", "Banerjee", "Mukherjee", "Pawar",
    "Chopra", "Saxena", "Trivedi", "Goyal", "Sinha", "Bhat", "Saini", "Pandey", "Kulkarni", "Desai",
]

# Curated showcase students (15th student in selected programs).
RISK_DEMO_PROFILES: dict[str, dict] = {
    "BSC-EMCS": {
        "name": "Priya Sharma",
        "age": 20,
        "gender": "F",
        "semester": 6,
        "attendance_pct": 92,
        "internal_marks": 78,
        "semester_marks": 81,
        "backlogs": 0,
        "fee_paid": "true",
        "fee_delay_days": 0,
        "financial_status": "medium",
        "family_background": "",
        "behavioral_indicators": "Punctual, participates actively",
        "extracurricular": "Coding club lead, hackathon winner",
        "placement_readiness": "high",
        "counselor_remarks": "Strong academic track; no intervention needed.",
        "risk_level": "low",
    },
    "BCA": {
        "name": "Rahul Mehta",
        "age": 20,
        "gender": "M",
        "semester": 5,
        "attendance_pct": 88,
        "internal_marks": 74,
        "semester_marks": 76,
        "backlogs": 0,
        "fee_paid": "true",
        "fee_delay_days": 0,
        "financial_status": "high",
        "family_background": "",
        "behavioral_indicators": "Collaborative, good peer feedback",
        "extracurricular": "Robotics club, internship completed",
        "placement_readiness": "high",
        "counselor_remarks": "On track for placement season.",
        "risk_level": "low",
    },
    "BSC-PCM": {
        "name": "Ananya Iyer",
        "age": 20,
        "gender": "F",
        "semester": 4,
        "attendance_pct": 95,
        "internal_marks": 82,
        "semester_marks": 84,
        "backlogs": 0,
        "fee_paid": "true",
        "fee_delay_days": 0,
        "financial_status": "medium",
        "family_background": "",
        "behavioral_indicators": "Consistent performer",
        "extracurricular": "NSS volunteer, technical paper presenter",
        "placement_readiness": "medium",
        "counselor_remarks": "Reliable attendance and steady grades.",
        "risk_level": "low",
    },
    "BSC-PMCS": {
        "name": "Vikram Singh",
        "age": 20,
        "gender": "M",
        "semester": 5,
        "attendance_pct": 68,
        "internal_marks": 52,
        "semester_marks": 54,
        "backlogs": 1,
        "fee_paid": "true",
        "fee_delay_days": 15,
        "financial_status": "medium",
        "family_background": "",
        "behavioral_indicators": "Missed two consecutive tutorials",
        "extracurricular": "Occasional lab sessions",
        "placement_readiness": "medium",
        "counselor_remarks": "Slipping attendance; one backlog to clear.",
        "risk_level": "medium",
    },
    "BSC-CBLS": {
        "name": "Sneha Patel",
        "age": 20,
        "gender": "F",
        "semester": 6,
        "attendance_pct": 73,
        "internal_marks": 53,
        "semester_marks": 55,
        "backlogs": 1,
        "fee_paid": "true",
        "fee_delay_days": 35,
        "financial_status": "medium",
        "family_background": "",
        "behavioral_indicators": "Quiet in class, limited office-hour visits",
        "extracurricular": "Workshop participant",
        "placement_readiness": "medium",
        "counselor_remarks": "Borderline grades and one backlog — monitor closely.",
        "risk_level": "medium",
    },
    "BBA": {
        "name": "Karan Joshi",
        "age": 20,
        "gender": "M",
        "semester": 4,
        "attendance_pct": 74,
        "internal_marks": 56,
        "semester_marks": 58,
        "backlogs": 1,
        "fee_paid": "true",
        "fee_delay_days": 0,
        "financial_status": "medium",
        "family_background": "",
        "behavioral_indicators": "Irregular lab submissions",
        "extracurricular": "Part-time tutoring",
        "placement_readiness": "medium",
        "counselor_remarks": "Needs academic coaching for backlog subject.",
        "risk_level": "medium",
    },
    "BSC-FS": {
        "name": "Arjun Reddy",
        "age": 20,
        "gender": "M",
        "semester": 5,
        "attendance_pct": 42,
        "internal_marks": 32,
        "semester_marks": 35,
        "backlogs": 4,
        "fee_paid": "false",
        "fee_delay_days": 90,
        "financial_status": "low",
        "family_background": "",
        "behavioral_indicators": "Repeated absences, disciplinary warning on file",
        "extracurricular": "",
        "placement_readiness": "low",
        "counselor_remarks": "Urgent intervention — multiple failed courses.",
        "risk_level": "high",
    },
    "BA-CPJ": {
        "name": "Meera Nair",
        "age": 20,
        "gender": "F",
        "semester": 6,
        "attendance_pct": 55,
        "internal_marks": 38,
        "semester_marks": 40,
        "backlogs": 3,
        "fee_paid": "false",
        "fee_delay_days": 120,
        "financial_status": "low",
        "family_background": "",
        "behavioral_indicators": "Late to exams, missed counseling appointment",
        "extracurricular": "",
        "placement_readiness": "low",
        "counselor_remarks": "Family financial stress reported; at risk of dropout.",
        "risk_level": "high",
    },
    "BSW": {
        "name": "Rohit Khan",
        "age": 20,
        "gender": "M",
        "semester": 4,
        "attendance_pct": 48,
        "internal_marks": 36,
        "semester_marks": 38,
        "backlogs": 3,
        "fee_paid": "false",
        "fee_delay_days": 60,
        "financial_status": "low",
        "family_background": "",
        "behavioral_indicators": "Disengaged, frequent class absences",
        "extracurricular": "",
        "placement_readiness": "low",
        "counselor_remarks": "Schedule parent meeting and remedial plan.",
        "risk_level": "high",
    },
}


def roll_prefix(code: str) -> str:
    return code.replace("-", "")


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


def make_random_row(rng: random.Random, dept_code: str, seq: int) -> dict:
    gender = rng.choice(GENDERS)
    is_pg = dept_code.startswith(("MA-", "MSC-", "MSW", "MBA", "MCA", "MCOM", "MTTM"))
    age = rng.randint(22, 28) if is_pg else rng.randint(17, 25)
    max_sem = 4 if is_pg else 8
    semester = rng.randint(1, max_sem)

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
    prefix = roll_prefix(dept_code)
    name = f"{rng.choice(FIRST)} {rng.choice(LAST)}"

    row = {
        "roll_no": f"{prefix}{semester:02d}{seq:04d}",
        "name": name,
        "age": age,
        "gender": gender,
        "department_code": dept_code,
        "semester": semester,
        "attendance_pct": round(attendance, 2),
        "internal_marks": round(internal, 1),
        "semester_marks": round(sem_marks, 1),
        "backlogs": backlogs,
        "fee_paid": "true" if fee_paid else "false",
        "fee_delay_days": fee_delay,
        "financial_status": financial,
        "family_background": rng.choice(["stable", "single parent", "joint family", "", "support: high"]),
        "behavioral_indicators": rng.choice(["", "", "calm", "warning: late submissions", "discipline: clean"]),
        "extracurricular": rng.choice(["", "music", "robotics club", "football, debate", "sports", "literary club"]),
        "placement_readiness": placement,
        "counselor_remarks": "",
    }
    row["risk_level"] = label_for(row)
    if rng.random() < 0.10:
        choices = [r for r in ("low", "medium", "high") if r != row["risk_level"]]
        row["risk_level"] = rng.choice(choices)
    return row


def make_demo_row(dept_code: str, profile: dict, seq: int) -> dict:
    prefix = roll_prefix(dept_code)
    semester = profile["semester"]
    row = {
        "roll_no": f"{prefix}{semester:02d}{seq:04d}",
        "department_code": dept_code,
        **{k: v for k, v in profile.items() if k != "semester"},
        "semester": semester,
    }
    return row


def main() -> int:
    rng = random.Random(42)
    out = Path(__file__).resolve().parents[1] / "datasets" / "sample_students.csv"
    rows: list[dict] = []

    for _name, code in DEPARTMENTS:
        for seq in range(1, 16):
            if seq == 15 and code in RISK_DEMO_PROFILES:
                rows.append(make_demo_row(code, RISK_DEMO_PROFILES[code], seq))
            else:
                rows.append(make_random_row(rng, code, seq))

    fields = list(rows[0].keys())
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows ({len(DEPARTMENTS)} programs x 15 students) -> {out}")
    demo_rolls = [
        make_demo_row(code, RISK_DEMO_PROFILES[code], 15)["roll_no"]
        for code in RISK_DEMO_PROFILES
    ]
    print("Risk demo roll numbers:", ", ".join(demo_rolls))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

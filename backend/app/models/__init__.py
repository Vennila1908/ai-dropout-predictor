"""SQLAlchemy ORM models. Importing this package registers them on Base.metadata."""

from app.models.audit_log import AuditLog
from app.models.counseling_session import CounselingSession
from app.models.department import Department
from app.models.faculty_note import FacultyNote
from app.models.prediction import Prediction
from app.models.recommendation import Recommendation
from app.models.risk_history import RiskHistory
from app.models.student import Student
from app.models.upload import Upload
from app.models.user import User

__all__ = [
    "AuditLog",
    "CounselingSession",
    "Department",
    "FacultyNote",
    "Prediction",
    "Recommendation",
    "RiskHistory",
    "Student",
    "Upload",
    "User",
]

"""Report generation endpoints — Excel + PDF."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.services import report_service


router = APIRouter(prefix="/reports", tags=["reports"], dependencies=[Depends(get_current_user)])


@router.get("/students.xlsx")
def students_xlsx(db: Session = Depends(get_db)) -> Response:
    data = report_service.students_xlsx(db)
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="students.xlsx"'},
    )


@router.get("/student/{student_id}.pdf")
def student_pdf(student_id: int, db: Session = Depends(get_db)) -> Response:
    data = report_service.student_pdf(db, student_id)
    if not data:
        raise HTTPException(status_code=404, detail="Student not found")
    return Response(
        content=data,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="student-{student_id}.pdf"'},
    )


@router.get("/department/{department_id}.pdf")
def department_pdf(department_id: int, db: Session = Depends(get_db)) -> Response:
    data = report_service.department_pdf(db, department_id)
    if not data:
        raise HTTPException(status_code=404, detail="Department not found")
    return Response(
        content=data,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="department-{department_id}.pdf"'},
    )

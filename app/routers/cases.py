from typing import Annotated
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.database import get_session
from app.models import Case, ReportSubmit, Employee, CaseClaim, CaseStatus, CaseRead

router = APIRouter(prefix="/cases", tags=["cases"])

SessionDep = Annotated[Session, Depends(get_session)]

def _case_to_read(case: Case, session: Session) -> CaseRead:
    """Builds the API-facing case representation, resolving claimedBy from
    the internal employee id to that employee's username."""
    claimed_by_username = None
    if case.claimedBy is not None:
        employee = session.get(Employee, case.claimedBy)
        if employee:
            claimed_by_username = employee.username
    return CaseRead(
        id=case.id,
        patientName=case.patientName,
        modality=case.modality,
        studyDate=case.studyDate,
        status=case.status,
        report=case.report,
        claimedAt=case.claimedAt,
        claimedBy=claimed_by_username,
    )

"""
the get_cases function returns all cases with a specified status and/or employee that has claimed the case
Results are ordered by ascending studyDate
"""
@router.get("")
async def get_cases(session: SessionDep, status: str = None, claimedBy: str = None):
    # TODO: sort by ascending studyDate and add filtering
    query = select(Case)
    if status is not None:
        query = query.where(Case.status == status)
    if claimedBy is not None:
        employee = session.exec(
            select(Employee).where(Employee.username == claimedBy)
        ).first()
        if not employee:
            # employee has no cases
            return {"data": []}
        query = query.where(Case.claimedBy == claimedBy)
    query = query.order_by(Case.studyDate)
    cases = session.exec(query).all()

    data = session.exec(select(Case)).all()
    return {"data": [_case_to_read(case, session) for case in cases]}


"""
the get_case function returns a case with a specified id
If the case is not found, a 404 error is raised.
"""
@router.get("/{id}")
async def get_case(session: SessionDep, id: int):
    case = session.get(Case, id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return {"data": _case_to_read(case, session)}


"""
claim_case transitions a case from PENDING to IN_PROGRESS, sets claimedAt to the current timestamp
and sets claimedBy to the employee id associated with the username
"""
@router.post("/{id}/claim")
async def claim_case(id: int, claimedBy: CaseClaim, session: SessionDep):
    case = session.get(Case, id)
    if not case:
        raise HTTPException(status_code=404, detail="case not found")
    if case.status != CaseStatus.PENDING:
        raise HTTPException(
            status_code=409,
            detail=f"case cannot be claimed from status {case.status.value}",
        )
    employee = session.exec(
        select(Employee).where(Employee.username == body.claimedBy)
    ).first()
    if not employee:
        raise HTTPException(status_code=404, detail="employee not found")

    case.status = CaseStatus.IN_PROGRESS
    case.claimedAt = datetime.now()
    case.claimedBy = employee.id

    session.add(case)
    session.commit()
    session.refresh(case)
    return {"data": _case_to_read(case, session)}

"""
report_case transitions a case from IN_PROGRESS to COMPLETED and stores the report text to the case
"""
#TODO: raise error if case not in IN_PROGRESS, report body is missing/empty,
# username missing
# username doesn't match claimedBy
@router.post("/{id}/report")
async def report_case(id: int, body: ReportSubmit, session: SessionDep):
    case = session.get(Case, id)
    if not case:
        raise HTTPException(status_code=404, detail="case not found")
    if case.status != CaseStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=409,
            detail=f"case cannot be reported from status {case.status.value}",
        )
    author = session.exec(
        select(Employee).where(Employee.username == body.author)
    ).first()
    if not author:
        raise HTTPException(status_code=404, detail="employee not found")
    if case.claimedBy != author.id:
        raise HTTPException(
            status_code=403,
            detail="only the employee who claimed this case may submit its report",
        )
    case.status = CaseStatus.COMPLETED
    case.report = body.report

    session.add(case)
    session.commit()
    session.refresh(case)
    return {"data": _case_to_read(case, session)}

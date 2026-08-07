from typing import Annotated
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.database import get_session
from app.models import Case, ReportSubmit, Employee, CaseClaim, CaseStatus, Modality

router = APIRouter(prefix="/cases", tags=["cases"])

SessionDep = Annotated[Session, Depends(get_session)]
"""
the get_cases function returns all cases with a specified status and/or employee that has claimed the case
Results are ordered by ascending studyDate
"""
@router.get("")
async def get_cases(session: SessionDep, status: str = None, claimedBy: str = None):
    # TODO: sort by ascending studyDate and add filtering
    data = session.exec(select(Case)).all()
    return {"data": data}


"""
the get_case function returns a case with a specified id
If the case is not found, a 404 error is raised.
"""
@router.get("/{id}")
async def get_case(session: SessionDep, id: int):
    case = session.get(Case, id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return {"data": case}


"""
claim_case transitions a case from PENDING to IN_PROGRESS, sets claimedAt to the current timestamp
and sets claimedBy to the employee id associated with the username
"""
# TODO: error if case not in pending, missing username/doesn't match existing employee
@router.post("/{id}/claim")
async def claim_case(id: int, claimedBy: CaseClaim, session: SessionDep):
    case = session.get(Case, id)
    if not case:
        raise HTTPException(status_code=404, detail="case not found")
    case.status = CaseStatus.IN_PROGRESS
    case.claimedAt = datetime.now()
    employee = session.get(Employee, claimedBy.username)
    case.claimedBy = employee.id
    session.add(case)
    session.commit()
    session.refresh(case)
    return {"data": case}

"""
report_case transitions a case from IN_PROGRESS to COMPLETED and stores the report text to the case
"""
#TODO: raise error if case not in IN_PROGRESS, report body is missing/empty,
# username missing
# username doesn't match claimedBy
@router.post("/{id}/report")
async def report_case(id: int, report: ReportSubmit, session: SessionDep):
    case = session.get(Case, id)
    if not case:
        raise HTTPException(status_code=404, detail="case not found")
    case.status = CaseStatus.COMPLETED
    case.report = report.report
    session.add(case)
    session.commit()
    session.refresh(case)
    return {"data": case}

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError

from app.database import get_session
from app.models import Employee, EmployeeCreate

router = APIRouter(prefix="/employees", tags=["employees"])

SessionDep = Annotated[Session, Depends(get_session)]

def _ensure_username_available(
    session: Session, username: str, exclude_id: int | None = None
) -> None:
    existing = session.exec(
        select(Employee).where(Employee.username == username)
    ).first()
    if existing and existing.id != exclude_id:
        raise HTTPException(status_code=409, detail="username already taken")

"""
get_employees returns all the employees in the database
"""
@router.get("")
async def get_employees(session: SessionDep):
    data = session.exec(select(Employee)).all()
    return data

"""
post_employee creates a new employee with the given username, which must be unique
"""
# TODO: make sure username is unique
@router.post("")
async def post_employee(session: SessionDep, employee: EmployeeCreate):
    _ensure_username_available(session, employee.username)
    db_employee = Employee.model_validate(employee)
    session.add(db_employee)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=409, detail="username already taken")
    session.refresh(db_employee)
    return db_employee

"""
update_employee updates the employees username by the id. the username must be unique
"""
# TODO: ensure that the username is unique, not missing/empty
@router.put("/{id}")
async def update_employee(id: int, session: SessionDep, employee: EmployeeCreate):
    db_employee = session.get(Employee, id)
    if not db_employee:
        raise HTTPException(status_code=404, detail="employee not found")
    _ensure_username_available(session, employee.username, exclude_id=id)
    db_employee.username = employee.username
    session.add(db_employee)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=409, detail="username already taken")
    session.refresh(db_employee)
    return db_employee

"""
delete_employee deletes the employee by their id
"""
@router.delete("/{id}")
async def delete_employee(id: int, session: SessionDep):
    db_employee = session.get(Employee, id)
    if not db_employee:
        raise HTTPException(status_code=404, detail="employee not found")
    session.delete(db_employee)
    session.commit()

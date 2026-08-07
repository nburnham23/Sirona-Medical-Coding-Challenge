from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.database import get_session
from app.models import Employee, EmployeeCreate

router = APIRouter(prefix="/employees", tags=["employees"])

SessionDep = Annotated[Session, Depends(get_session)]

"""
get_employees returns all the employees in the database
"""
@router.get("")
async def get_employees(session: SessionDep):
    data = session.exec(select(Employee)).all()
    return {"data": data}

"""
post_employee creates a new employee with the given username, which must be unique
"""
# TODO: make sure username is unique
@router.post("")
async def post_employee(session: SessionDep, employee: EmployeeCreate):
    db_employee = Employee.model_validate(employee)
    session.add(db_employee)
    session.commit()
    session.refresh(db_employee)
    return {"data": db_employee}

"""
update_employee updates the employees username by the id. the username must be unique
"""
# TODO: ensure that the username is unique, not missing/empty
@router.put("/{id}")
async def update_employee(id: int, session: SessionDep, employee: EmployeeCreate):
    db_employee = session.get(Employee, id)
    if not employee:
        raise HTTPException(status_code=404, detail="employee not found")
    db_employee.username = employee.username
    session.add(db_employee)
    session.commit()
    session.refresh(db_employee)
    return {"data": db_employee}

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

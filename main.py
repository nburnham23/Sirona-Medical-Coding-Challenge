from fastapi import FastAPI, HTTPException, Response, Request, Depends
from typing import Any, Annotated, Generic, TypeVar
from datetime import datetime
from random import randint

from contextlib import asynccontextmanager
from pydantic import BaseModel

from sqlmodel import create_engine, Session, SQLModel, select, Field

class Case(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    patientName: str = Field(default=None)
    modality: str = Field(default=None)
    studyDate: datetime = Field(default=None)
    status: str = Field(default=None, index=True)
    report: str | None = Field(default=None)
    claimedAt: datetime | None = Field(default=None)
    claimedBy: int | None = Field(default=None, index=True)

class Employee(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    username: str = Field(default=None, index=True)

class EmployeeCreate(BaseModel):
    username: str

class CaseClaim(BaseModel):
    claimedBy: str

class ReportSubmit(BaseModel):
    author: str
    report: str


sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    with Session(engine) as session:
        if not session.exec(select(Case)).first(): # if the db is empty, seed it w sample data
            session.add_all([
                Case(
                    id=1,
                    patientName="Noah Burnham",
                    modality="CT",
                    studyDate=datetime.now(),
                    status="PENDING",
                    report="",
                    claimedAt=datetime.now(),
                ),
                Case(
                    id=2,
                    patientName="Charles Charlie",
                    modality="US",
                    studyDate=datetime.now(),
                    status="IN_PROGRESS",
                    report="",
                    claimedAt=datetime.now(),
                    claimedBy=15
                )
            ])
            session.commit()
    yield

app = FastAPI(lifespan=lifespan)


@app.get("/")
def root():
    return {"message": "Hello World"}

"""
the get_cases function returns all cases with a specified status and/or employee that has claimed the case
Results are ordered by ascending studyDate
"""
@app.get("/cases")
async def get_cases(session: SessionDep, status: str = None, claimedBy: str = None):
    # TODO: sort by ascending studyDate and add filtering
    data = session.exec(select(Case)).all()
    return {"data": data}


"""
the get_case function returns a case with a specified id
If the case is not found, a 404 error is raised.
"""
@app.get("/cases/{id}")
async def get_case(session: SessionDep, id: int):
    case = session.get(Case, id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return {"data": case}


"""
get_employees returns all the employees in the database
"""
@app.get("/employees")
async def get_employees(session: SessionDep):
    data = session.exec(select(Employee)).all()
    return {"data": data}

"""
post_employee creates a new employee with the given username, which must be unique
"""
# TODO: make sure username is unique
@app.post("/employees")
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
@app.put("/employees/{id}")
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
@app.delete("/employees/{id}")
async def delete_employee(id: int, session: SessionDep):
    db_employee = session.get(Employee, id)
    if not db_employee:
        raise HTTPException(status_code=404, detail="employee not found")
    session.delete(db_employee)
    session.commit()

"""
claim_case transitions a case from PENDING to IN_PROGRESS, sets claimedAt to the current timestamp
and sets claimedBy to the employee id associated with the username
"""
# TODO: error if case not in pending, missing username/doesn't match existing employee
@app.post("/cases/{id}/claim")
async def claim_case(id: int, claimedBy: CaseClaim, session: SessionDep):
    case = session.get(Case, id)
    if not case:
        raise HTTPException(status_code=404, detail="case not found")
    case.status = "IN_PROGRESS"
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
# username missing/doesn't match existing employee,
# username doesn't match claimedBy
@app.post("/cases/{id}/report")
async def report_case(id: int, report: ReportSubmit, session: SessionDep):
    case = session.get(Case, id)
    if not case:
        raise HTTPException(status_code=404, detail="case not found")
    case.status = "COMPLETED"
    case.report = report.report
    session.add(case)
    session.commit()
    session.refresh(case)
    return {"data": case}








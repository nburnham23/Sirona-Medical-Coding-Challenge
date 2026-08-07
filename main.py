from fastapi import FastAPI, HTTPException, Depends
from typing import Annotated
from datetime import datetime

from contextlib import asynccontextmanager

from sqlmodel import create_engine, Session, SQLModel, select, Field

from app.models import Case, Employee, CaseStatus, Modality
from app.database import engine, get_session
from app.routers import cases, employees

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

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
                    modality=Modality.CT,
                    studyDate=datetime.now(),
                    status=CaseStatus.PENDING,
                    report="",
                    claimedAt=datetime.now(),
                ),
                Case(
                    id=2,
                    patientName="Charles Charlie",
                    modality=Modality.US,
                    studyDate=datetime.now(),
                    status=CaseStatus.IN_PROGRESS,
                    report="",
                    claimedAt=datetime.now(),
                    claimedBy=15
                )
            ])
            session.commit()
    yield

app = FastAPI(lifespan=lifespan)
app.include_router(cases.router)
app.include_router(employees.router)


@app.get("/")
def root():
    return {"message": "Hello World"}












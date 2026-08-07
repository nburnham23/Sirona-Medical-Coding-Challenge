from datetime import date, datetime

from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlmodel import Session, SQLModel, select

from app.models import Case, Employee, Modality, CaseStatus
from app.database import engine
from app.routers import cases, employees


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    with Session(engine) as session:
        if not session.exec(select(Employee)).first():  # if the db is empty, seed it w sample data
            seeded_employees = [
                Employee(username="jsmith"),
                Employee(username="agarcia"),
                Employee(username="mchen"),
            ]
            session.add_all(seeded_employees)
            session.commit()
            for employee in seeded_employees:
                session.refresh(employee)
            jsmith, agarcia, mchen = seeded_employees

            session.add_all([
                Case(
                    patientName="Jane Smith",
                    modality=Modality.CT,
                    studyDate=date(2024, 11, 1),
                    status=CaseStatus.PENDING,
                ),
                Case(
                    patientName="Noah Burnham",
                    modality=Modality.MRI,
                    studyDate=date(2024, 11, 2),
                    status=CaseStatus.PENDING,
                ),
                Case(
                    patientName="Charles Charlie",
                    modality=Modality.XR,
                    studyDate=date(2024, 11, 3),
                    status=CaseStatus.PENDING,
                ),
                Case(
                    patientName="Maria Lopez",
                    modality=Modality.US,
                    studyDate=date(2024, 11, 4),
                    status=CaseStatus.IN_PROGRESS,
                    claimedAt=datetime(2024, 11, 4, 9, 0),
                    claimedBy=jsmith.id,
                ),
                Case(
                    patientName="David Kim",
                    modality=Modality.CT,
                    studyDate=date(2024, 11, 5),
                    status=CaseStatus.IN_PROGRESS,
                    claimedAt=datetime(2024, 11, 5, 10, 0),
                    claimedBy=agarcia.id,
                ),
                Case(
                    patientName="Priya Patel",
                    modality=Modality.MRI,
                    studyDate=date(2024, 11, 6),
                    status=CaseStatus.COMPLETED,
                    claimedAt=datetime(2024, 11, 6, 8, 30),
                    claimedBy=mchen.id,
                    report="No acute findings.",
                ),
                Case(
                    patientName="Tom Nguyen",
                    modality=Modality.XR,
                    studyDate=date(2024, 11, 7),
                    status=CaseStatus.COMPLETED,
                    claimedAt=datetime(2024, 11, 7, 13, 15),
                    claimedBy=jsmith.id,
                    report="Findings consistent with mild degenerative changes.",
                ),
                Case(
                    patientName="Ella Rodriguez",
                    modality=Modality.US,
                    studyDate=date(2024, 11, 8),
                    status=CaseStatus.PENDING,
                ),
            ])
            session.commit()
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(cases.router)
app.include_router(employees.router)


@app.get("/")
def root():
    return {"message": "Hello World"}
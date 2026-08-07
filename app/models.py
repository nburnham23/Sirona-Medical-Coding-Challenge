from datetime import datetime

from pydantic import BaseModel
from sqlmodel import Field, SQLModel

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
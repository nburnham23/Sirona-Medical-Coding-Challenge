from datetime import datetime, date

from pydantic import BaseModel, ConfigDict, Field as PydanticField
from sqlmodel import Field, SQLModel
from enum import Enum

class Modality(str, Enum):
    CT = "CT"
    MRI = "MRI"
    XR = "XR"
    US = "US"

class CaseStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"

class Case(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    patientName: str = Field(default=None)
    modality: Modality = Field(default=None)
    studyDate: datetime = Field(default=None)
    status: CaseStatus = Field(default=None, index=True)
    report: str | None = Field(default=None)
    claimedAt: datetime | None = Field(default=None)
    claimedBy: int | None = Field(default=None, index=True)

class Employee(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    username: str = Field(default=None, index=True)

class EmployeeCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    username: str = PydanticField(min_length=1)

class CaseClaim(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    claimedBy: str = PydanticField(min_length=1)

class ReportSubmit(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    author: str = PydanticField(min_length=1)
    report: str = PydanticField(min_length=1)

class CaseRead(BaseModel):
    id: int
    patientName: str
    modality: Modality
    studyDate: date
    status: CaseStatus
    report: str | None
    claimedAt: datetime | None
    claimedBy: str | None
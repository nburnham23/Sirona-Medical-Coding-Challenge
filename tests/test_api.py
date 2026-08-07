from datetime import date, datetime

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.database import get_session
from app.models import Case, CaseStatus, Employee, Modality
from main import app


@pytest.fixture(name="session")
def session_fixture():
    # Fresh in-memory SQLite per test. StaticPool keeps the same connection
    # alive for the whole test (a plain in-memory DB would otherwise vanish
    # between connections).
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    # Not using `with TestClient(app) as client` on purpose: that would run
    # the app's lifespan, which seeds the *production* engine/database.
    # Tests build their own fixtures against the isolated test session instead.
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def make_employee(session: Session, username: str) -> Employee:
    employee = Employee(username=username)
    session.add(employee)
    session.commit()
    session.refresh(employee)
    return employee


def make_case(session: Session, **overrides) -> Case:
    defaults = dict(
        patientName="Test Patient",
        modality=Modality.CT,
        studyDate=date(2024, 11, 1),
        status=CaseStatus.PENDING,
    )
    defaults.update(overrides)
    case = Case(**defaults)
    session.add(case)
    session.commit()
    session.refresh(case)
    return case


# ---------------------------------------------------------------------------
# claim
# ---------------------------------------------------------------------------

def test_claim_pending_case_succeeds(session, client):
    make_employee(session, "jsmith")
    case = make_case(session, status=CaseStatus.PENDING)

    response = client.post(f"/cases/{case.id}/claim", json={"claimedBy": "jsmith"})

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "IN_PROGRESS"
    assert data["claimedBy"] == "jsmith"
    assert data["claimedAt"] is not None


def test_claim_in_progress_case_fails(session, client):
    employee = make_employee(session, "jsmith")
    case = make_case(session, status=CaseStatus.IN_PROGRESS, claimedBy=employee.id)

    response = client.post(f"/cases/{case.id}/claim", json={"claimedBy": "jsmith"})

    assert response.status_code == 409


def test_claim_completed_case_fails(session, client):
    employee = make_employee(session, "jsmith")
    case = make_case(
        session, status=CaseStatus.COMPLETED, claimedBy=employee.id, report="done"
    )

    response = client.post(f"/cases/{case.id}/claim", json={"claimedBy": "jsmith"})

    assert response.status_code == 409


def test_claim_missing_username_fails(session, client):
    case = make_case(session, status=CaseStatus.PENDING)

    response = client.post(f"/cases/{case.id}/claim", json={"claimedBy": ""})

    assert response.status_code == 422


def test_claim_unknown_username_fails(session, client):
    case = make_case(session, status=CaseStatus.PENDING)

    response = client.post(f"/cases/{case.id}/claim", json={"claimedBy": "ghost"})

    assert response.status_code == 404


def test_claim_nonexistent_case_fails(client):
    response = client.post("/cases/999/claim", json={"claimedBy": "jsmith"})
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# report
# ---------------------------------------------------------------------------

def test_report_in_progress_case_succeeds(session, client):
    employee = make_employee(session, "jsmith")
    case = make_case(
        session,
        status=CaseStatus.IN_PROGRESS,
        claimedBy=employee.id,
        claimedAt=datetime.now(),
    )

    response = client.post(
        f"/cases/{case.id}/report",
        json={"author": "jsmith", "report": "All clear."},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "COMPLETED"
    assert data["report"] == "All clear."


def test_report_pending_case_fails(session, client):
    make_employee(session, "jsmith")
    case = make_case(session, status=CaseStatus.PENDING)

    response = client.post(
        f"/cases/{case.id}/report",
        json={"author": "jsmith", "report": "All clear."},
    )

    assert response.status_code == 409


def test_report_completed_case_fails(session, client):
    employee = make_employee(session, "jsmith")
    case = make_case(
        session,
        status=CaseStatus.COMPLETED,
        claimedBy=employee.id,
        report="already done",
    )

    response = client.post(
        f"/cases/{case.id}/report",
        json={"author": "jsmith", "report": "All clear."},
    )

    assert response.status_code == 409


def test_report_empty_body_fails(session, client):
    employee = make_employee(session, "jsmith")
    case = make_case(session, status=CaseStatus.IN_PROGRESS, claimedBy=employee.id)

    response = client.post(
        f"/cases/{case.id}/report",
        json={"author": "jsmith", "report": ""},
    )

    assert response.status_code == 422


def test_report_by_non_claiming_employee_fails(session, client):
    claimant = make_employee(session, "jsmith")
    make_employee(session, "agarcia")
    case = make_case(session, status=CaseStatus.IN_PROGRESS, claimedBy=claimant.id)

    response = client.post(
        f"/cases/{case.id}/report",
        json={"author": "agarcia", "report": "All clear."},
    )

    assert response.status_code == 403


def test_report_unknown_author_fails(session, client):
    employee = make_employee(session, "jsmith")
    case = make_case(session, status=CaseStatus.IN_PROGRESS, claimedBy=employee.id)

    response = client.post(
        f"/cases/{case.id}/report",
        json={"author": "ghost", "report": "All clear."},
    )

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# listing / filtering / ordering
# ---------------------------------------------------------------------------

def test_get_cases_orders_by_study_date_ascending(session, client):
    make_case(session, patientName="Later", studyDate=date(2024, 11, 5))
    make_case(session, patientName="Earlier", studyDate=date(2024, 11, 1))
    make_case(session, patientName="Middle", studyDate=date(2024, 11, 3))

    response = client.get("/cases")

    assert response.status_code == 200
    names = [c["patientName"] for c in response.json()["data"]]
    assert names == ["Earlier", "Middle", "Later"]


def test_get_cases_filters_by_status(session, client):
    make_case(session, patientName="A", status=CaseStatus.PENDING)
    employee = make_employee(session, "jsmith")
    make_case(
        session, patientName="B", status=CaseStatus.IN_PROGRESS, claimedBy=employee.id
    )

    response = client.get("/cases", params={"status": "PENDING"})

    names = [c["patientName"] for c in response.json()["data"]]
    assert names == ["A"]


def test_get_cases_filters_by_claimed_by_username(session, client):
    jsmith = make_employee(session, "jsmith")
    agarcia = make_employee(session, "agarcia")
    make_case(
        session,
        patientName="Claimed by jsmith",
        status=CaseStatus.IN_PROGRESS,
        claimedBy=jsmith.id,
    )
    make_case(
        session,
        patientName="Claimed by agarcia",
        status=CaseStatus.IN_PROGRESS,
        claimedBy=agarcia.id,
    )

    response = client.get("/cases", params={"claimedBy": "jsmith"})

    names = [c["patientName"] for c in response.json()["data"]]
    assert names == ["Claimed by jsmith"]


def test_get_case_not_found(client):
    response = client.get("/cases/999")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# employees
# ---------------------------------------------------------------------------

def test_create_employee_succeeds(client):
    response = client.post("/employees", json={"username": "jsmith"})
    assert response.status_code == 200
    assert response.json()["data"]["username"] == "jsmith"


def test_create_employee_duplicate_username_fails(session, client):
    make_employee(session, "jsmith")

    response = client.post("/employees", json={"username": "jsmith"})

    assert response.status_code == 409


def test_create_employee_empty_username_fails(client):
    response = client.post("/employees", json={"username": "   "})
    assert response.status_code == 422


def test_update_employee_nonexistent_fails(client):
    response = client.put("/employees/999", json={"username": "newname"})
    assert response.status_code == 404


def test_update_employee_to_taken_username_fails(session, client):
    make_employee(session, "jsmith")
    other = make_employee(session, "agarcia")

    response = client.put(f"/employees/{other.id}", json={"username": "jsmith"})

    assert response.status_code == 409


def test_delete_employee_nonexistent_fails(client):
    response = client.delete("/employees/999")
    assert response.status_code == 404
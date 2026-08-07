from fastapi import FastAPI, HTTPException, Response
from typing import Any
from datetime import datetime
from random import randint

app = FastAPI()

cases: Any = [
    {
        "id": 1,
        "patientName": "John smith",
        "modality": "CT",
        "studyDate": datetime.now(),
        "status": "PENDING",
        "report": "null until submited...",
        "claimedAt": datetime.now(),
        "claimedBy": 45
    },
    {
        "id": 2,
        "patientName": "Sallie Churchill",
        "modality": "US",
        "studyDate": datetime.now(),
        "status": "IN_PROGRESS",
        "report": "null until submited...",
        "claimedAt": datetime.now(),
        "claimedBy": 23
    }
]

employees: Any = [
    {
        "id": 45,
        "username": "nburnham"
    },
    {
        "id": 23,
        "username": "jsmith"
    }
]

@app.get("/")
def root():
    return {"message": "Hello World"}

"""
the get_cases function returns all cases with a specified status and/or employee that has claimed the case
Results are ordered by ascending studyDate
"""
@app.get("/cases")
async def get_cases(status: str = None, claimedBy: int = None):
    return {"cases": cases}

"""
the get_case function returns a case with a specified id
If the case is not found, a 404 error is raised.
"""
@app.get("/cases/{id}")
async def get_case(id: int):
    for case in cases:
        if case.get("id") == id:
            return case
    raise HTTPException(status_code=404, detail="Case not found")

@app.get("/employees")
async def get_employees():
    return {"employees": employees}

@app.post("/employees")
async def post_employee(username: str):
    new_employee = {
        "id": randint(1, 10000),
        "username": username
    }
    employees.append(new_employee)
    return {"employee": new_employee}

@app.put("/employees/{id}")
async def put_employee(id: int, username: str):
    for index, employee in enumerate(employees):
        if employee.get("id") == id:
            updated_employee = {
                "id": id,
                "username": username
            }
            employees[index] = updated_employee
            return {"employee": updated_employee}
    raise HTTPException(status_code=404, detail="employee not found")

@app.delete("/employees/{id}")
async def delete_employee(id: int):
    for index, employee in enumerate(employees):
        if employee.get("id") == id:
            employees.pop(index)
            return Response(status_code=204)
    raise HTTPException(status_code=404, detail="employee not found")


@app.post("/cases/{id}/claim")
async def claim_case(id: int, claimedBy: str):
    for case in cases:
        if case.get("id") == id:
            case["status"] = "IN_PROGRESS"
            case["claimedAt"] = datetime.now()
            for employee in employees:
                if employee.get("username") == claimedBy:
                    employee_id = employee.get("id")
                    case["claimedBy"] = employee_id
                    return {"case": case}
            raise HTTPException(status_code=404, detail="employee not found")
    raise HTTPException(status_code=404, detail="case not found")

@app.post("/cases/{id}/report")
async def report_case(id: int, body: dict[str, Any]):
    for index, case in enumerate(cases):
        if case.get("id") == id:
            case["report"] = body.get("report")
            case["status"] = "COMPLETED"
            return {"case": case}
    raise HTTPException(status_code=404, detail="case not found")







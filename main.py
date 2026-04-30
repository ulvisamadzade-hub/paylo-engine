from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from calculator import calculate_batch
from payroll_runner import run_payroll

app = FastAPI()


class Employee(BaseModel):
    employee_id: str
    base_salary: float
    vacation_pay: float = 0
    ot_earnings: float = 0
    hr_adjustment: float = 0
    vacation_deduction: float = 0


class BatchRequest(BaseModel):
    employees: List[Employee]


class RunPayrollRequest(BaseModel):
    period_id: str
    company_id: str
    employee_ids: Optional[List[str]] = None


@app.api_route("/health", methods=["GET", "HEAD"])
def health():
    return {"status": "ok"}


@app.post("/calculate")
def calculate(request: BatchRequest):
    employees = [emp.dict() for emp in request.employees]
    results = calculate_batch(employees)
    return {"results": results}


@app.post("/run-payroll")
def run_payroll_endpoint(request: RunPayrollRequest):
    try:
        result = run_payroll(
            period_id=request.period_id,
            company_id=request.company_id,
            employee_ids=request.employee_ids,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

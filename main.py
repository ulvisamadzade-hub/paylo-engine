from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import json
import os
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

class RawBatchRequest(BaseModel):
    employees_json: str | List[dict] = []

@app.get("/")
def root():
    return {"status": "Paylo Engine running"}

@app.post("/calculate")
def calculate(request: BatchRequest):
    employees = [emp.dict() for emp in request.employees]
    results = calculate_batch(employees)
    return {"results": results}

class ArrayBatchRequest(BaseModel):
    employees: List[dict] = []

@app.post("/calculate/from-bubble")
def calculate_from_bubble(request: ArrayBatchRequest):
    results = calculate_batch(request.employees)
    return {"results": results}

class RunPayrollRequest(BaseModel):
    snapshot_id: str
    bubble_api_key: str
    app_url: Optional[str] = None

@app.post("/run-payroll")
def run_payroll_endpoint(request: RunPayrollRequest):
    try:
        result = run_payroll(request.snapshot_id, request.bubble_api_key, request.app_url)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

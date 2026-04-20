from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
import json
from calculator import calculate_batch

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
    employees_json: str  # JSON string Bubble builds as text

@app.get("/")
def root():
    return {"status": "Paylo Engine running"}

@app.post("/calculate")
def calculate(request: BatchRequest):
    employees = [emp.dict() for emp in request.employees]
    results = calculate_batch(employees)
    return {"results": results}

@app.post("/calculate/from-bubble")
def calculate_from_bubble(request: RawBatchRequest):
    try:
        employees = json.loads(request.employees_json)
    except (json.JSONDecodeError, TypeError):
        employees = []
    results = calculate_batch(employees)
    return {"results": results}

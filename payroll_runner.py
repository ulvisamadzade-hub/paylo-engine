from bubble_client import BubbleClient
from calculator import calculate_payslip

def run_payroll(snapshot_id: str, api_key: str, app_url: str = None) -> dict:
    client = BubbleClient(api_key, app_url)

    snapshot = client.get_snapshot(snapshot_id)
    period_id = snapshot["payroll_period"]
    company_id = snapshot["company"]

    period = client.get_payroll_period(period_id)
    working_hours = period.get("working_hours", 168)

    employees = client.get_active_employees(company_id)
    ot_entries = client.get_overtime_entries(period_id, company_id)
    leave_requests = client.get_leave_requests(period_id, company_id)
    existing_totals = client.get_existing_snapshot_totals(snapshot_id)

    # Index by employee ID for fast lookup
    ot_by_employee = {}
    for ot in ot_entries:
        emp_id = ot["employee"]
        ot_by_employee.setdefault(emp_id, []).append(ot)

    leave_by_employee = {}
    for lr in leave_requests:
        emp_id = lr["employee"]
        leave_by_employee.setdefault(emp_id, []).append(lr)

    existing_by_employee = {t["employee"]: t for t in existing_totals}

    results = []
    for emp in employees:
        emp_id = emp["_id"]
        base_salary = emp.get("base_salary_amount", 0) or 0

        # Calculate OT earnings
        ot_earnings = sum(
            ot.get("approved_hours", 0) * base_salary / working_hours
            for ot in ot_by_employee.get(emp_id, [])
        )

        # Calculate vacation pay and deduction from leave requests
        vacation_pay = sum(
            lr.get("vacation_amount", 0) or 0
            for lr in leave_by_employee.get(emp_id, [])
        )
        vacation_deduction = sum(
            (lr.get("working_days_on_leave", 0) or 0) * base_salary / (working_hours / 8)
            for lr in leave_by_employee.get(emp_id, [])
        )

        payslip = calculate_payslip({
            "employee_id": emp_id,
            "base_salary": base_salary,
            "vacation_pay": round(vacation_pay, 2),
            "ot_earnings": round(ot_earnings, 2),
            "hr_adjustment": 0,
            "vacation_deduction": round(vacation_deduction, 2)
        })

        record_data = {
            "employee": emp_id,
            "payroll_snapshot": snapshot_id,
            "company": company_id,
            "base_salary_snapshot": base_salary,
            "gross_salary": payslip["gross_salary"],
            "vacation_pay": payslip["vacation_pay"],
            "ot_earnings": payslip["ot_earnings"],
            "hr_adjustment": payslip["hr_adjustment"],
            "vacation_deduction": payslip["vacation_deduction"],
            "total_gross": payslip["total_gross"],
            "income_tax": payslip["income_tax"],
            "dsmf_employee": payslip["dsmf_employee"],
            "dsmf_employer": payslip["dsmf_employer"],
            "med_ins_employee": payslip["med_ins_employee"],
            "med_ins_employer": payslip["med_ins_employer"],
            "unemployment_employee": payslip["unemployment_employee"],
            "unemployment_employer": payslip["unemployment_employer"],
            "total_deductions": payslip["total_deductions"],
            "net_salary": payslip["net_salary"]
        }

        if emp_id in existing_by_employee:
            client.update_snapshot_total(existing_by_employee[emp_id]["_id"], record_data)
        else:
            client.create_snapshot_total(record_data)

        results.append({"employee_id": emp_id, "net_salary": payslip["net_salary"]})

    return {"status": "complete", "processed": len(results), "snapshot_id": snapshot_id}

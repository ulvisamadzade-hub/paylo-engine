from datetime import datetime
from supabase_client import SupabaseClient
from calculator import calculate_payslip


def _is_weekend(date_str: str) -> bool:
    return datetime.fromisoformat(date_str).weekday() >= 5


def run_payroll(period_id: str, company_id: str, employee_ids: list = None) -> dict:
    db = SupabaseClient()

    period = db.get_payroll_period(period_id)
    if not period:
        raise ValueError(f"Period {period_id} not found")

    working_hours = period.get("working_hours") or 168
    working_days = working_hours / 8
    period_start = period["period_start"]
    period_end = period["period_end"]

    employees = db.get_active_employees(company_id, employee_ids)
    if not employees:
        return {"calculated": 0, "errors": []}

    emp_ids = [e["id"] for e in employees]
    snapshot_id = db.get_or_create_snapshot(period_id, company_id)

    ot_entries = db.get_approved_ot(period_start, period_end, emp_ids)
    leave_entries = db.get_approved_leave(period_id, emp_ids)

    # Index by employee
    ot_by_emp: dict[str, list] = {}
    for ot in ot_entries:
        ot_by_emp.setdefault(ot["employee_id"], []).append(ot)

    leave_by_emp: dict[str, list] = {}
    for lr in leave_entries:
        leave_by_emp.setdefault(lr["employee_id"], []).append(lr)

    calculated = 0
    errors = []

    for emp in employees:
        emp_id = emp["id"]
        base_salary = float(emp.get("base_salary_amount") or 0)
        hourly_rate = base_salary / working_hours
        daily_rate = base_salary / working_days

        try:
            # OT: 1.5x weekday, 2x weekend
            ot_earnings = 0.0
            for ot in ot_by_emp.get(emp_id, []):
                hours = float(ot.get("hours") or 0)
                rate = 2.0 if _is_weekend(ot["date"]) else 1.5
                ot_earnings += hours * hourly_rate * rate

            # Leave
            vacation_pay = 0.0
            sick_pay = 0.0
            vacation_deduction = 0.0

            for lr in leave_by_emp.get(emp_id, []):
                leave_type = lr.get("leave_type", "")
                days = float(lr.get("working_days_on_leave") or 0)
                deduction = round(days * daily_rate, 2)

                if leave_type == "ANNUAL":
                    vacation_pay += float(lr.get("vacation_amount") or 0)
                    vacation_deduction += deduction
                elif leave_type == "SICK":
                    sick_pay += float(lr.get("sick_pay_amount") or 0)
                    vacation_deduction += deduction
                elif leave_type == "UNPAID":
                    vacation_deduction += deduction

            payslip = calculate_payslip({
                "employee_id": emp_id,
                "base_salary": base_salary,
                "vacation_pay": round(vacation_pay + sick_pay, 2),
                "ot_earnings": round(ot_earnings, 2),
                "hr_adjustment": 0,
                "vacation_deduction": round(vacation_deduction, 2),
            })

            total_row = {
                "payroll_snapshot_id": snapshot_id,
                "employee_id": emp_id,
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
                "net_salary": payslip["net_salary"],
            }

            total = db.upsert_snapshot_total(total_row)

            db.upsert_payslip({
                "payroll_snapshot_id": snapshot_id,
                "employee_id": emp_id,
                "version": 1,
                "snapshot_employee_total_id": total["id"],
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
                "net_salary": payslip["net_salary"],
            })

            calculated += 1

        except Exception as e:
            errors.append({"employee_id": emp_id, "error": str(e)})

    return {"calculated": calculated, "errors": errors}

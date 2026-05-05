import logging
from datetime import datetime, date as date_type
from supabase_client import SupabaseClient
from calculator import calculate_payslip

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


def _is_weekend(date_str: str) -> bool:
    return datetime.fromisoformat(date_str).weekday() >= 5


def _working_days_in_range(start_str: str, end_str: str) -> int:
    """Count Mon–Fri days between two ISO date strings inclusive."""
    s = date_type.fromisoformat(str(start_str)[:10])
    e = date_type.fromisoformat(str(end_str)[:10])
    return sum(1 for i in range((e - s).days + 1) if (s.toordinal() + i) % 7 < 5)


def _leave_working_days(start_str: str, end_str: str, holidays: set) -> int:
    """Count Mon–Fri days in leave period excluding public holidays."""
    s = date_type.fromisoformat(str(start_str)[:10])
    e = date_type.fromisoformat(str(end_str)[:10])
    count = 0
    for i in range((e - s).days + 1):
        d = date_type.fromordinal(s.toordinal() + i)
        if d.weekday() < 5 and d.isoformat() not in holidays:
            count += 1
    return count


def run_payroll(period_id: str, company_id: str, employee_ids: list = None) -> dict:
    log.info("run_payroll start period=%s company=%s", period_id, company_id)
    db = SupabaseClient()
    log.info("supabase client created")

    period = db.get_payroll_period(period_id)
    if not period:
        raise ValueError(f"Period {period_id} not found")
    log.info("period fetched: %s → %s", period.get("period_start"), period.get("period_end"))

    period_start = period["period_start"]
    period_end = period["period_end"]
    working_hours = period.get("working_hours") or 168
    working_days_in_period = _working_days_in_range(period_start, period_end)

    employees = db.get_active_employees(company_id, employee_ids)
    log.info("employees fetched: %d", len(employees))
    if not employees:
        return {"calculated": 0, "errors": []}

    emp_ids = [e["id"] for e in employees]
    snapshot_id = db.get_or_create_snapshot(period_id, company_id)
    log.info("snapshot_id=%s", snapshot_id)

    log.info("fetching OT...")
    ot_entries = db.get_approved_ot(period_start, period_end, emp_ids)
    log.info("OT entries: %d", len(ot_entries))

    log.info("fetching leave...")
    leave_entries = db.get_approved_leave(period_start, period_end, emp_ids)
    log.info("leave entries: %d", len(leave_entries))

    log.info("fetching holidays...")
    holidays = db.get_public_holidays(period_start, period_end)
    log.info("holidays: %d", len(holidays))

    log.info("fetching hr adjustments...")
    adj_entries = db.get_hr_adjustments(period_id, emp_ids)
    adj_by_emp = {a["employee_id"]: float(a["amount"]) for a in adj_entries}
    log.info("hr adjustments: %d", len(adj_by_emp))

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
        daily_rate = base_salary / working_days_in_period

        try:
            # OT: 1.5x weekday, 2x weekend
            ot_earnings = 0.0
            for ot in ot_by_emp.get(emp_id, []):
                hours = float(ot.get("hours") or 0)
                rate = 2.0 if _is_weekend(ot["date"]) else 1.5
                ot_earnings += hours * hourly_rate * rate

            # Leave (ANNUAL/SICK = full salary preserved; UNPAID = deduct working days)
            vacation_pay = 0.0
            vacation_deduction = 0.0

            for lr in leave_by_emp.get(emp_id, []):
                leave_type = lr.get("leave_type", "")
                start_str = str(lr["start_date"])[:10]
                end_str = str(lr["end_date"])[:10]

                try:
                    s = date_type.fromisoformat(start_str)
                    e = date_type.fromisoformat(end_str)
                    total_days = (e - s).days + 1
                    holiday_count = sum(1 for h in holidays if start_str <= h <= end_str)
                    # Pay: all calendar days excluding holidays (incl. weekends)
                    vacation_days = total_days - holiday_count
                    # Deduction: Mon–Fri days excluding holidays only
                    leave_working_days = _leave_working_days(start_str, end_str, holidays)
                except Exception:
                    vacation_days = float(lr.get("working_days_on_leave") or 0)
                    leave_working_days = vacation_days

                deduction = round(leave_working_days * daily_rate, 2)

                if leave_type == "ANNUAL":
                    # Full salary preserved — no pay addition, no deduction
                    pass
                elif leave_type == "SICK":
                    # Full salary preserved — no pay addition, no deduction
                    pass
                elif leave_type == "UNPAID":
                    vacation_deduction += deduction

            payslip = calculate_payslip({
                "employee_id": emp_id,
                "base_salary": base_salary,
                "vacation_pay": round(vacation_pay, 2),
                "ot_earnings": round(ot_earnings, 2),
                "hr_adjustment": round(adj_by_emp.get(emp_id, 0.0), 2),
                "vacation_deduction": round(vacation_deduction, 2),
            })

            total_row = {
                "payroll_snapshot_id": snapshot_id,
                "company_id": company_id,
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
                "company_id": company_id,
                "employee_id": emp_id,
                "payroll_period_id": period_id,
                "version": 1,
                "snapshot_employee_totals_id": total.get("id"),
                "status": "DRAFT",
            })

            calculated += 1

        except Exception as e:
            errors.append({"employee_id": emp_id, "error": str(e)})

    return {"calculated": calculated, "errors": errors}

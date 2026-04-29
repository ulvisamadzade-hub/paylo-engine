import os
from supabase import create_client, Client


def _get_client() -> Client:
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    return create_client(url, key)


class SupabaseClient:
    def __init__(self):
        self.db: Client = _get_client()

    # ── Reads ──────────────────────────────────────────────────

    def get_payroll_period(self, period_id: str) -> dict:
        res = (
            self.db.table("payroll_periods")
            .select("id, period_start, period_end, working_hours, company_id")
            .eq("id", period_id)
            .single()
            .execute()
        )
        return res.data

    def get_active_employees(self, company_id: str, employee_ids: list = None) -> list:
        q = (
            self.db.table("employees")
            .select("id, full_name, base_salary_amount, department_id")
            .eq("company_id", company_id)
            .eq("is_active", True)
        )
        if employee_ids:
            q = q.in_("id", employee_ids)
        return q.execute().data or []

    def get_approved_ot(
        self, period_start: str, period_end: str, employee_ids: list
    ) -> list:
        if not employee_ids:
            return []
        return (
            self.db.table("overtime_requests")
            .select("employee_id, hours, date")
            .in_("employee_id", employee_ids)
            .eq("status", "approved")
            .gte("date", period_start)
            .lte("date", period_end)
            .execute()
            .data
            or []
        )

    def get_approved_leave(
        self, period_start: str, period_end: str, employee_ids: list
    ) -> list:
        if not employee_ids:
            return []
        # Match any leave that overlaps with the period
        return (
            self.db.table("leave_requests")
            .select(
                "employee_id, leave_type, start_date, end_date, "
                "working_days_on_leave, vacation_amount, sick_pay_amount"
            )
            .in_("employee_id", employee_ids)
            .lte("start_date", period_end)
            .gte("end_date", period_start)
            .eq("status", "APPROVED")
            .execute()
            .data
            or []
        )

    def get_public_holidays(self, period_start: str, period_end: str) -> set:
        """Return a set of ISO date strings that are public holidays in the range."""
        res = (
            self.db.table("public_holidays")
            .select("date")
            .gte("date", period_start)
            .lte("date", period_end)
            .execute()
        )
        return {row["date"] for row in (res.data or [])}

    # ── Snapshot management ────────────────────────────────────

    def get_or_create_snapshot(self, period_id: str, company_id: str) -> str:
        """Reuse the latest snapshot for this period, or create a fresh one."""
        existing = (
            self.db.table("payroll_snapshots")
            .select("id")
            .eq("payroll_period_id", period_id)
            .eq("company_id", company_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
            .data
        )
        if existing:
            return existing[0]["id"]

        res = (
            self.db.table("payroll_snapshots")
            .insert(
                {
                    "company_id": company_id,
                    "payroll_period_id": period_id,
                    "status": "DRAFT",
                }
            )
            .execute()
        )
        return res.data[0]["id"]

    # ── Writes ─────────────────────────────────────────────────

    def upsert_snapshot_total(self, data: dict) -> dict:
        res = (
            self.db.table("snapshot_employee_totals")
            .upsert(data, on_conflict="payroll_snapshot_id,employee_id")
            .execute()
        )
        return res.data[0] if res.data else {}

    def upsert_payslip(self, data: dict) -> None:
        (
            self.db.table("payslips")
            .upsert(data, on_conflict="payroll_snapshot_id,employee_id,version")
            .execute()
        )

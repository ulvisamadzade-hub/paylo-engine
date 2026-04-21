import httpx
from typing import Optional

BUBBLE_API_BASE = "https://paylo.bubbleapps.io/api/1.1"

class BubbleClient:
    def __init__(self, api_key: str, app_url: Optional[str] = None):
        self.headers = {"Authorization": f"Bearer {api_key}"}
        self.base = app_url or BUBBLE_API_BASE

    def _get_all(self, data_type: str, constraints: list = None, fields: list = None) -> list:
        results = []
        cursor = 0
        limit = 100
        while True:
            params = {"limit": limit, "cursor": cursor}
            if constraints:
                import json
                params["constraints"] = json.dumps(constraints)
            r = httpx.get(f"{self.base}/obj/{data_type}", headers=self.headers, params=params)
            r.raise_for_status()
            data = r.json()["response"]
            results.extend(data["results"])
            if len(results) >= data["count"] or len(data["results"]) < limit:
                break
            cursor += limit
        return results

    def get_snapshot(self, snapshot_id: str) -> dict:
        r = httpx.get(f"{self.base}/obj/payrollsnapshot/{snapshot_id}", headers=self.headers)
        r.raise_for_status()
        return r.json()["response"]

    def get_payroll_period(self, period_id: str) -> dict:
        r = httpx.get(f"{self.base}/obj/payrollperiod/{period_id}", headers=self.headers)
        r.raise_for_status()
        return r.json()["response"]

    def get_active_employees(self, company_id: str) -> list:
        return self._get_all("employee", constraints=[
            {"key": "is_active", "constraint_type": "equals", "value": True},
            {"key": "company", "constraint_type": "equals", "value": company_id}
        ])

    def get_overtime_entries(self, period_id: str, company_id: str) -> list:
        entries = self._get_all("overtimeentry", constraints=[
            {"key": "payroll_period", "constraint_type": "equals", "value": period_id},
            {"key": "company", "constraint_type": "equals", "value": company_id}
        ])
        return [e for e in entries if e.get("status") == "Təsdiqləndi"]

    def get_leave_requests(self, period_id: str, company_id: str) -> list:
        requests = self._get_all("leaverequest", constraints=[
            {"key": "original_period", "constraint_type": "equals", "value": period_id},
            {"key": "company", "constraint_type": "equals", "value": company_id}
        ])
        return [r for r in requests if r.get("status") == "Təsdiqləndi"]

    def get_existing_snapshot_totals(self, snapshot_id: str) -> list:
        return self._get_all("snapshotemployeetotals", constraints=[
            {"key": "payroll_snapshot", "constraint_type": "equals", "value": snapshot_id}
        ])

    def create_snapshot_total(self, data: dict) -> dict:
        r = httpx.post(f"{self.base}/obj/snapshotemployeetotals",
                       headers=self.headers, json=data)
        r.raise_for_status()
        return r.json() if r.text else {}

    def update_snapshot_total(self, record_id: str, data: dict) -> dict:
        r = httpx.patch(f"{self.base}/obj/snapshotemployeetotals/{record_id}",
                        headers=self.headers, json=data)
        r.raise_for_status()
        return r.json() if r.text else {}

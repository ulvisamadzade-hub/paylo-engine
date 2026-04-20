import requests
import random
import time

employees = []
for i in range(800):
    employees.append({
        "employee_id": f"EMP-{i+1}",
        "base_salary": random.uniform(600, 15000),
        "vacation_pay": random.uniform(0, 2000),
        "ot_earnings": random.uniform(0, 500),
        "hr_adjustment": 0,
        "vacation_deduction": random.uniform(0, 300)
    })

start = time.time()
response = requests.post(
    "http://127.0.0.1:8000/calculate",
    json={"employees": employees}
)
end = time.time()

results = response.json()["results"]
print(f"\n✅ Employees calculated: {len(results)}")
print(f"⏱  Time taken: {round(end - start, 3)} seconds")
print(f"\nSample — {results[0]['employee_id']}:")
print(f"  Total gross: {results[0]['total_gross']}")
print(f"  Net salary:  {results[0]['net_salary']}")

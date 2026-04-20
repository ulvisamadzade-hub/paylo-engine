from calculator import calculate_payslip, calculate_batch

# Test 1 - Fatima (matches your Bubble data)
fatima = {
    "employee_id": "EMP-4",
    "base_salary": 2750,
    "vacation_pay": 2550,
    "ot_earnings": 93.75,
    "hr_adjustment": 0,
    "vacation_deduction": 500
}

result = calculate_payslip(fatima)
print("\n=== FATIMA ===")
for key, value in result.items():
    print(f"{key}: {value}")

# Test 2 - Batch with all employees
employees = [
    {"employee_id": "EMP-1", "base_salary": 8500, "vacation_pay": 0, "ot_earnings": 0, "hr_adjustment": 0, "vacation_deduction": 0},
    {"employee_id": "EMP-2", "base_salary": 15000, "vacation_pay": 0, "ot_earnings": 0, "hr_adjustment": 0, "vacation_deduction": 0},
    {"employee_id": "EMP-3", "base_salary": 6000, "vacation_pay": 0, "ot_earnings": 0, "hr_adjustment": 0, "vacation_deduction": 0},
    {"employee_id": "EMP-4", "base_salary": 2750, "vacation_pay": 2550, "ot_earnings": 93.75, "hr_adjustment": 0, "vacation_deduction": 500},
    {"employee_id": "EMP-5", "base_salary": 3000, "vacation_pay": 0, "ot_earnings": 0, "hr_adjustment": 0, "vacation_deduction": 0},
    {"employee_id": "EMP-6", "base_salary": 5000, "vacation_pay": 0, "ot_earnings": 0, "hr_adjustment": 0, "vacation_deduction": 0},
]

print("\n=== BATCH RESULTS ===")
batch = calculate_batch(employees)
for emp in batch:
    print(f"\n{emp['employee_id']} → gross: {emp['total_gross']} | tax: {emp['income_tax']} | net: {emp['net_salary']}")

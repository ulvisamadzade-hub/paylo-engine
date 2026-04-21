def calculate_income_tax(gross):
    if gross <= 2500:
        return round(gross * 0.03, 2)
    elif gross <= 8000:
        return round(75 + (gross - 2500) * 0.10, 2)
    else:
        return round(625 + (gross - 8000) * 0.14, 2)

def calculate_dsmf_employee(gross):
    if gross <= 200:
        return round(gross * 0.03, 2)
    elif gross <= 8000:
        return round(6 + (gross - 200) * 0.10, 2)
    else:
        return round(gross * 0.10 - 14, 2)

def calculate_dsmf_employer(gross):
    if gross <= 200:
        return round(gross * 0.22, 2)
    elif gross <= 8000:
        return round(44 + (gross - 200) * 0.15, 2)
    else:
        return round(gross * 0.11, 2)

def calculate_medical_employee(gross):
    if gross <= 2500:
        return round(gross * 0.02, 2)
    else:
        return round(50 + (gross - 2500) * 0.005, 2)

def calculate_medical_employer(gross):
    if gross <= 2500:
        return round(gross * 0.02, 2)
    else:
        return round(50 + (gross - 2500) * 0.005, 2)

def calculate_unemployment_employee(gross):
    return round(gross * 0.005, 2)

def calculate_unemployment_employer(gross):
    return round(gross * 0.005, 2)

def calculate_payslip(employee):
    base_salary = employee.get("base_salary", 0)
    vacation_pay = employee.get("vacation_pay", 0)
    ot_earnings = employee.get("ot_earnings", 0)
    hr_adjustment = employee.get("hr_adjustment", 0)
    vacation_deduction = employee.get("vacation_deduction", 0)

    gross_salary = base_salary - vacation_deduction
    total_gross = gross_salary + vacation_pay + ot_earnings + hr_adjustment

    income_tax = calculate_income_tax(total_gross)
    dsmf_employee = calculate_dsmf_employee(total_gross)
    dsmf_employer = calculate_dsmf_employer(total_gross)
    med_ins_employee = calculate_medical_employee(total_gross)
    med_ins_employer = calculate_medical_employer(total_gross)
    unemployment_employee = calculate_unemployment_employee(total_gross)
    unemployment_employer = calculate_unemployment_employer(total_gross)

    total_deductions = (income_tax + dsmf_employee + 
                       med_ins_employee + unemployment_employee)

    net_salary = total_gross - total_deductions

    return {
        "employee_id": employee.get("employee_id"),
        "gross_salary": gross_salary,
        "vacation_pay": vacation_pay,
        "ot_earnings": ot_earnings,
        "hr_adjustment": hr_adjustment,
        "vacation_deduction": vacation_deduction,
        "total_gross": total_gross,
        "income_tax": income_tax,
        "dsmf_employee": dsmf_employee,
        "dsmf_employer": dsmf_employer,
        "med_ins_employee": med_ins_employee,
        "med_ins_employer": med_ins_employer,
        "unemployment_employee": unemployment_employee,
        "unemployment_employer": unemployment_employer,
        "total_deductions": total_deductions,
        "net_salary": net_salary
    }

def calculate_batch(employees):
    return [calculate_payslip(emp) for emp in employees]

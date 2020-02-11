# Payroll

## Get a list of employee payments for selected period 

**URL** : `/api/employers/me/employee-payment-list/<period_id>`

**Method** : `GET`

**Auth required** : Yes

**Permissions required** : Authenticated User, User should be an Employer

#### Request Params:

Any

#### Example

http://localhost:5000/api/employers/me/employee-payment-list/1

#### Success Response

**Code** : `200 OK`

**Content examples**

```json
{
    "employer": {
        "id": 1,
        "title": "Fetes and Events",
        "status": "APROVED",
        "bank_accounts": [{"id": 1, "name": "EmployerBankAcc", "institution_name": "Bank of America",
                            "account": "personal", "account_id": "1234567890123"}
                         ]
    },
    "payroll_period": 1,
    "payments": [{"id": 4, "employee": {"first_name": "John", "last_name": "Lennon", 
                                        "bank_accounts": [{"id": 1, "name": "EmployerBankAcc", 
                                        "institution_name": "Bank of America", "account": "personal", "account_id": "1234567890123"}]
                                        }, 
                  "regular_hours": "3.00", "over_time": "2.00", "earnings": "150.00", "deductions": 37.8, "amount": 112.2,
                  "paid": false, "payroll_period": 1, 
                  "deduction_list": [{"name": "Social Security", "amount": 7.5}, {"name": "Medicare", "amount": 7.5}, 
                                     {"name": "DeductionTest", "amount": 22.8}]
                 },
                  ...
                ]
}
```

#### Notes

- Deduction values are calculate on fly.


## Proceed with payment of an employee in a period 

**URL** : `/api/employers/me/employee-payment/<employee_payment_id>`

**Method** : `POST`

**Auth required** : Yes

**Permissions required** : Authenticated User, User should be an Employer

#### Request Params:

| key             | Example Value                     | Required?     | Observations                          |
| --------------  | --------------------------------  | ------------- | ------------------------------------- |
| payment_type    |  "ELECTRONIC TRANSFERENCE"        |     Yes       | CHECK, ELECTRONIC TRANSFERENCE, FAKE  |
|                 |                                   |               | FAKE imitate a real electronic transference |
| payment_data    |  {"employer_bank_account_id": 3   |     Yes       | Dict, can be empty                    |
|                 |   "employee_bank_account_id": 7}  |               | For ELECTRONIC TRANSFERENCE type,     |
|                 |                                   |               | employer_bank_account_id and          |
|                 |                                   |               | employee_bank_account_id              |
|                 |                                   |               | keys are required                     |

#### Example

http://localhost:5000/api/employers/me/employee-payment/3

#### Success Response

**Code** : `200 OK`

**Content examples**

```json
{
    "message": "success"
}
```

#### Notes

- Bank account Ids are provided via endpoint `api/employers/me/employee-payment-list/<period_id>`.
- Values for `amount`, `deductions` and `deduction_list` fields are updated. 
- A registry in **PaymentTransaction** model is created, related **PayrrolPeriodPayment** and **PayrollPeriod** registries are set as PAID.

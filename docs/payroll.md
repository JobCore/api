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
                  "regular_hours": "3.00", "over_time": "2.00", 
                  "earnings": "150.00", "deductions": 37.8, "taxes": 4.15, "amount": 108.05,
                  "paid": false, "payroll_period": 1, 
                  "deduction_list": [{"name": "Social Security", "amount": 7.5}, {"name": "Medicare", "amount": 7.5}, 
                                     {"name": "DeductionTest", "amount": 22.8}]
                 },
                  ...
                ]
}
```

#### Notes

- Deduction and taxes values are calculate on fly.


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
|                 |   "employee_bank_account_id": 7}  |               | For ELECTRONIC TRANSFERENCE and FAKE types,     |
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
- Values for `amount`, `taxes`, `deductions` and `deduction_list` fields are updated. 
- A registry in **PaymentTransaction** model is created, related **PayrrolPeriodPayment** and **PayrollPeriod** registries are set as PAID.
- Related PayrollPeriod is set as PAID.


## Get a list of EmployeePayment instances with paid status and belong to current employer

**URL** : `/api/employers/me/employee-payment/report`

**Method** : `GET`

**Auth required** : Yes

**Permissions required** : Authenticated User, User should be an Employer

#### Request Params:

| key           | Example Value           | Required?     | Observations                                  |
| ------------  | ----------------------  | ------------- | --------------------------------------------- |
| period_id     |  1                      |     No        | This parameter has precedence over others     |
| start_date    |  2020-01-15             |     No        |                                               |
| end_date      |  2020-01-31             |     No        |                                               |

#### Example

http://localhost:5000/api/employers/me/employee-payment/report?period_id=1
http://localhost:5000/api/employers/me/employee-payment/report?start_date=2020-01-28

#### Success Response

**Code** : `200 OK`

**Content examples**

```json
[
  {
    "employee": "Lennon, John",
    "earnings": "150.00",
    "deductions": "37.80",
    "taxes": "4.15",
    "amount": "108.05",
    "payment_date": "2020-02-13",
    "payment_source": "ELECTRONIC TRANSFERENCE",
    "payroll_period": 
      {
        "id": 1,
        "starting_at": "2019-02-09T00:00:00Z",
        "ending_at": "2019-02-16T00:00:00Z"
      },
  },
  ...
]
```

#### Notes

- If `period_id` reference a PayrollPeriod which don't belong to authenticated user(employer), 
an error about not existence of PayrollPeriod is returned
- API can handle null value in GET parameters without problem 


## Get a list of data deductions related to a paid EmployeePayment and belong to current employer

**URL** : `/api/employers/me/employee-payment/deduction-report`

**Method** : `GET`

**Auth required** : Yes

**Permissions required** : Authenticated User, User should be an Employer

#### Request Params:

| key           | Example Value           | Required?     | Observations                                  |
| ------------  | ----------------------  | ------------- | --------------------------------------------- |
| period_id     |  1                      |     No        | This parameter has precedence over others     |
| start_date    |  2020-01-15             |     No        |                                               |
| end_date      |  2020-01-31             |     No        |                                               |

#### Example

http://localhost:5000/api/employers/me/employee-payment/deduction-report?period=1
http://localhost:5000/api/employers/me/employee-payment/deduction-report?start_date=2020-01-28

#### Success Response

**Code** : `200 OK`

**Content examples**

```json
[
  {
    "employee": "Lennon, John",
    "deduction_amount": "37.80",
    "deduction_list": [
        {
          "name": "Social Security",
          "amount": "7.5000"
        },
        {
          "name": "Medicare",
          "amount": "7.5000"
        },
        ...
    ],
    "taxes": "2.50",
    "payment_date": "2020-02-13",
    "payroll_period": 
      {
        "id": 1,
        "starting_at": "2019-02-09T00:00:00Z",
        "ending_at": "2019-02-16T00:00:00Z"
      },
  },
  ...
]
```

#### Notes

- If `period_id` reference a PayrollPeriod which don't belong to authenticated user(employer), 
an error about not existence of PayrollPeriod is returned
- API can handle null value in GET parameters without problem

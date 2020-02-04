# PayrollPeriods

## Create periods for employers

**URL** : `/api/hook/generate_periods`

**Method** : `GET`

**Auth required** : NO

**Permissions required** : Any

#### Request Params:

| key            | Example Value      | Required?     | Observations           |
| -------------  | -----------------  | ------------- | ---------------------- |
| employer       |      1             |     No        | Id of employer to use  |


#### Example

http://localhost:5000/api/hook/generate_periods?employer=1

#### Success Response

**Code** : `200 OK`

**Content examples**

```json
[
{
    "id": 3,
    "employer": {
        "title": "Fetes and Events",
        "id": 1,
        "picture": "",
        "rating": "0.0",
        "total_ratings": 0
    },
    "length": 7,
    "length_type": "DAYS",
    "status": "OPEN",
    "starting_at": "2020-01-28T16:45:01Z",
    "ending_at": "2020-02-04T16:45:00Z",
    "created_at": "2020-02-04T19:47:50.384469Z",
    "payments": [{"id": 8, "approved_clockin_time": null, "approved_clockout_time": null, "breaktime_minutes": 0,
                  "clockin": { ... }, "created_at": "2020-02-04T19:53:10.741Z", "employee": { ... }, "employer": { ... },
                  "hourly_rate": "15.00", "over_time": "0.00", "regular_hours": "3.00", "total_amount": "45.00", 
                  "payroll_period": 3, "shift": { ... }, "splited_payment": false, "status": "PENDING",
                  "updated_at": "2020-02-04T19:53:10.638Z"
                 },
                  ...
                ]
},
...
]
```

#### Notes

- Create PayrollPeriod instances for all employers with payroll_period_starting_time value; periods are created from date of last existing period.
- Additional to creation of PayrollPeriod instances, PayrollPeriodPayment instances will be created if there are Clockin instances with dates belong to created period


## GET periods for all employers

**URL** : `/api/periods`

**Method** : `GET`

**Auth required** : YES

**Permissions required** : Authenticated User

#### Request Params:

| key            | Example Value      | Required?     | Observations             |
| -------------  | -----------------  | ------------- | ------------------------ |
| employer       | 1                  |     No        | Id of employer to use    |
| status         | OPEN               |     No        | OPEN, FINALIZED or PAID  |


#### Example

http://localhost:5000/api/periods?status=OPEN

#### Success Response

**Code** : `200 OK`

**Content examples**

```json
[
{
    "id": 3,
    "employer": {
        "title": "Fetes and Events",
        "id": 1,
        "picture": "",
        "rating": "0.0",
        "total_ratings": 0
    },
    "length": 7,
    "length_type": "DAYS",
    "status": "OPEN",
    "starting_at": "2020-01-28T16:45:01Z",
    "ending_at": "2020-02-04T16:45:00Z",
    "created_at": "2020-02-04T19:47:50.384469Z",
    "payments": [{"id": 8, "approved_clockin_time": null, "approved_clockout_time": null, "breaktime_minutes": 0,
                  "clockin": { ... }, "created_at": "2020-02-04T19:53:10.741Z", "employee": { ... }, "employer": { ... },
                  "hourly_rate": "15.00", "over_time": "0.00", "regular_hours": "3.00", "total_amount": "45.00", 
                  "payroll_period": 3, "shift": { ... }, "splited_payment": false, "status": "PENDING",
                  "updated_at": "2020-02-04T19:53:10.638Z"
                 },
                  ...
                ]
},
...
]
```


## GET a period of any employer

**URL** : `/api/periods/<period_id>`

**Method** : `GET`

**Auth required** : YES

**Permissions required** : Authenticated User

#### Request Params:

Any

#### Example

http://localhost:5000/api/periods/3

#### Success Response

**Code** : `200 OK`

**Content examples**

```json
{
    "id": 3,
    "employer": {
        "title": "Fetes and Events",
        "id": 1,
        "picture": "",
        "rating": "0.0",
        "total_ratings": 0
    },
    "length": 7,
    "length_type": "DAYS",
    "status": "OPEN",
    "starting_at": "2020-01-28T16:45:01Z",
    "ending_at": "2020-02-04T16:45:00Z",
    "created_at": "2020-02-04T19:47:50.384469Z",
    "payments": [{"id": 8, "approved_clockin_time": null, "approved_clockout_time": null, "breaktime_minutes": 0,
                  "clockin": { ... }, "created_at": "2020-02-04T19:53:10.741Z", "employee": { ... }, "employer": { ... },
                  "hourly_rate": "15.00", "over_time": "0.00", "regular_hours": "3.00", "total_amount": "45.00", 
                  "payroll_period": 3, "shift": { ... }, "splited_payment": false, "status": "PENDING",
                  "updated_at": "2020-02-04T19:53:10.638Z"
                 },
                  ...
                ]
}
```


## GET a list of periods belong to me

**URL** : `/api/employers/me/payroll-periods`

**Method** : `GET`

**Auth required** : YES

**Permissions required** : Authenticated User, User should be an Employer

#### Request Params:

Any

#### Example

http://localhost:5000/api/employers/me/payroll-periods

#### Success Response

**Code** : `200 OK`

**Content examples**

```json
[
{
    "id": 1,
    "status": "OPEN",
    "starting_at": "2020-01-21T13:52:01Z",
    "ending_at": "2020-01-28T13:52:00Z",
    "created_at": "2020-02-03T22:43:52.3892Z",
    "payments": [{"id": 6, "approved_clockin_time": "2020-01-22T10:00:00Z", "approved_clockout_time": "2020-01-22T11:30:00Z", 
                  "breaktime_minutes": 0, "clockin": { ... }, "created_at": "2020-01-22T10:00:00Z", 
                  "employee": { ... }, "employer": { ... },
                  "hourly_rate": "25.00", "over_time": "1.00", "regular_hours": "3.00", "total_amount": "100.00", 
                  "payroll_period": 1, "shift": { ... }, "splited_payment": false, "status": "PENDING",
                  "updated_at": "2020-02-03T22:43:52.3892" 
                 },
                  ...
                ]
},
...
]
```


## GET a period belong to me

**URL** : `/api/employers/me/payroll-periods/<period_id>`

**Method** : `GET`

**Auth required** : YES

**Permissions required** : Authenticated User, User should be an Employer

#### Request Params:

Any

#### Example

http://localhost:5000/api/employers/me/payroll-periods/3

#### Success Response

**Code** : `200 OK`

**Content examples**

```json
{
    "id": 3,
    "employer": {
        "title": "Fetes and Events",
        "id": 1,
        "picture": "",
        "rating": "0.0",
        "total_ratings": 0
    },
    "length": 7,
    "length_type": "DAYS",
    "status": "OPEN",
    "starting_at": "2020-01-28T16:45:01Z",
    "ending_at": "2020-02-04T16:45:00Z",
    "created_at": "2020-02-04T19:47:50.384469Z",
    "payments": [{"id": 8, "approved_clockin_time": "2020-01-29T09:30:00Z", "approved_clockout_time": "2020-01-29T11:45:00Z", 
                  "breaktime_minutes": 0, "clockin": { ... }, "created_at": "2020-01-29T09:30:00Z", 
                  "employee": { ... }, "employer": { ... },
                  "hourly_rate": "20.00", "over_time": "2.00", "regular_hours": "3.00", "total_amount": "100.00", 
                  "payroll_period": 3, "shift": { ... }, "splited_payment": false, "status": "PENDING",
                  "updated_at": "2020-01-29T11:45:00Z"
                 },
                  ...
                ]
}
```


## Finalize a period belong to me

**URL** : `/api/employers/me/payroll-periods/<period_id>`

**Method** : `PUT`

**Auth required** : YES

**Permissions required** : Authenticated User, User should be an Employer

#### Request Params:

| key          | Example Value      | Required?     | Observations           |
| -----------  | -----------------  | ------------- | ---------------------- |
| status       | FINALIZED          |     Yes       |                        |

#### Example

http://localhost:5000/api/employers/me/payroll-periods/3

#### Success Response

**Code** : `200 OK`

**Content examples**

```json
{
    "id": 3,
    "length": 7,
    "length_type": "DAYS",
    "status": "FINALIZED",
    "starting_at": "2020-01-28T16:45:01Z",
    "ending_at": "2020-02-04T16:45:00Z",
    "created_at": "2020-02-04T19:47:50.384469Z",
    "updated_at": "2020-02-04T19:47:50.384469Z",
    "employer": 1
}
```

#### Notes

- You must be the owner of the PayrollPeriod to update.
- There will be created instances of EmployeePayment, using PayrollPeriodPayment instances with APPROVED status 
and belong to indicated PayrollPeriod and related Employer. 
- Even if OPEN value is send in status parameter, the period is set to FINALIZED.

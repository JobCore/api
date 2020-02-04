# Deductions

## Create a new deduction

**URL** : `/api/employers/me/deduction`

**Method** : `POST`

**Auth required** : YES

**Permissions required** : Authenticated User, User should be an Employer

#### Request Params:

| key                   | Example Value      | Required?     | Observations         |
| --------------------  | -----------------  | ------------- | -------------------- |
| name                  |  "Test Deduction"  |     Yes       |                      |
| value                 |  10.0              |     Yes       | Float Value          |
| type                  |   "PERCENTAGE"     |     No        |PERCENTAGE or AMOUNT, default to PERCENTAGE  |
| description           |  "Some Description"|     Yes       |                      |


#### Example

http://localhost:5000/api/employers/me/deduction

#### Success Response

**Code** : `201 Created`

**Content examples**

```json
{
    "id": 1,
    "name": "Test Deduction",
    "value": 10.0,
    "type": "PERCENTAGE",
    "description": "Some Description",
    "lock": false,
    "employer": 1
}
```


## List my  deductions

**URL** : `/api/employers/me/deduction`

**Method** : `GET`

**Auth required** : YES

**Permissions required** : Authenticated User, User should be an Employer

#### Example

http://localhost:5000/api/employers/me/deduction

#### Success Response

**Code** : `200 OK`

**Content examples**

```json
[
    {
        "id": 1,
        "name": "Deduction1",
        "value": 12.3,
        "type": "PERCENTAGE",
        "description": "Some Description",
        "lock": false,
        "employer": 1
    }
            ...
]
```

#### Notes

- Deduction list include predefined deductions (**PreDefinedDeduction** model)


## Delete Deduction

**URL** : `/api/employers/me/deduction/<id>`

**Method** : `DELETE`

**Auth required** : YES

**Permissions required** : Authenticated User, User should be an Employer

#### Example

http://localhost:5000/api/employers/me/deduction/1

#### Success Response

**Code** : `202 Accepted`

**Content examples**

```json
{"detail": "Object Deleted"}
```

#### Notes

- You must be the owner of the deduction, and the deduction must be locked = False


## Update Deduction

**URL** : `/api/employers/me/deduction/<id>`

**Method** : `PUT`

**Auth required** : YES

**Permissions required** : Authenticated User, User should be an Employer

#### Example:

http://localhost:5000/api/employers/me/deduction/1


#### Request Params


| key                   | Example Value         | Required?     | Observations         |
| --------------------  | --------------------  | ------------- | -------------------- |
| name                  |  "My Test Deduction"  |     No        |                      |
| value                 |  12.5                 |     No        | Float Value          |
| description           |  "Some Description"   |     No        |                      |


#### Success Response

**Code** : `200 OK`

**Content examples**

```json
{
    "id": 1,
    "name": "My Test Deduction",
    "value": 12.5,
    "type": "PERCENTAGE",
    "description": "Some Description",
    "lock": false,
    "employer": 1
}
```

#### Notes

- You must be the owner of the deduction, and the deduction must be locked = False

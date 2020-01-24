# Deductions

## Create a new deduction

**URL** : `/api/employers/me/deduction`

**Method** : `POST`

**Auth required** : YES

**Permissions required** : Authenticated User

## Request Params


| key                   | Example Value      | Required?     | Observations         |
| --------------------  | -----------------  | ------------- | -------------------- |
| name                  |  "Test Deduction"  |     Yes       |                      |
| value                 |  10.0              |     Yes       | Float Value          |
| type                  |   "PERCENTAGE"     |     No        |PERCENTAGE or AMOUNT, default to PERCENTAGE  |
| description           |  "Some Description"|     No        |                      |



## List my  deductions

**URL** : `/api/employers/me/deduction`

**Method** : `GET`

**Auth required** : YES

**Permissions required** : Authenticated User

## Example:

http://localhost:5000/api/employers/me/deduction

## Success Response

**Code** : `200 OK`

**Content examples**


```json
[
    {
        "name": " name",
        "value": 123,
        "type": "PERCENTAGE",
        "description": "Somne Description",
    }
            ...
]
```

## Notes


## Delete Deduction

**URL** : `/api/employers/me/deduction/<id>`

**Method** : `DELETE`

**Auth required** : YES

**Permissions required** : Authenticated User

## Example:

http://localhost:5000/api/employers/me/deduction/1

## Success Response

**Code** : `202 OK`

**Content examples**


## Notes

- You must


## Update Deduction

**URL** : `/api/employers/me/deduction/<id>`

**Method** : `PUT`

**Auth required** : YES

**Permissions required** : Authenticated User

## Example:

http://localhost:5000/api/employers/me/deduction/1


## Request Params


| key                   | Example Value      | Required?     | Observations         |
| --------------------  | -----------------  | ------------- | -------------------- |
| name                  |  "Test Deduction"  |     Yes       |                      |
| value                 |  10.0              |     Yes       | Float Value          |
| description           |  "Some Description"|     No        |                      |


## Success Response

**Code** : `202 OK`

**Content examples**


## Notes

- You must be the owner of the deduction, and the deduction must be locked = False
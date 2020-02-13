# Bank Accounts

## Create a new bank account

**URL** : `/api/bank-accounts`

**Method** : `POST`

**Auth required** : YES

**Permissions required** : Authenticated User, User should be an Employer or Employee

## Request Params


| key                   | Example Value | Required?     |
| --------------------  | ------------  | ------------- |
| public_token          |  "" |     Yes       |


## Example:

http://localhost:5000/api/bank-accounts

## Success Response

**Code** : `200 OK`

**Content examples**


```json

```

## Notes

## List my bank accounts

**URL** : `/api/bank-accounts`

**Method** : `GET`

**Auth required** : YES

**Permissions required** : Authenticated User

## Example:

http://localhost:5000/api/bank-accounts

## Success Response

**Code** : `200 OK`

**Content examples**


```json
[
    {
        "name": " name",
        "id": 123,
    }
            ...
]
```

## Notes
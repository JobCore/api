# Bank Accounts

## Create a new bank account

**URL** : `/api/bank-accounts`

**Method** : `POST`

**Auth required** : YES

**Permissions required** : Authenticated User

## Request Params


| key                   | Example Value | Required?     |
| --------------------  | ------------  | ------------- |
| public_token          |  "" |     Yes       |
| account_id            |  "" |     Yes       |
| account_name          |  "" |      No       |
| institution_name      |  "" |      No       |


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
        "institution_name":"Institution Name",
        "name": " name",
        "id": 123,
    }
            ...
]
```

## Notes
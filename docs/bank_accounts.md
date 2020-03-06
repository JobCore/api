# Bank Accounts

## Create a new bank account

**URL** : `/api/bank-accounts`

**Method** : `POST`

**Auth required** : YES

**Permissions required** : Authenticated User, User should be an Employer or Employee

#### Request Params

| key                   | Example Value                                          | Required?     |
| --------------------  | -----------------------------------------------------  | ------------- |
| public_token          |  "public-sandbox-b8f386fc-c730-46a7-bd08-efe6afeb9922" |     Yes       |

#### Example:

http://localhost:5000/api/bank-accounts

#### Success Response

**Code** : `200 OK`

**Content examples**

```json
{
    "success": "created!"
}
```

#### Notes

- For employee, his profile must have birth_date and last_4dig_ssn values.


## List my bank accounts

**URL** : `/api/bank-accounts`

**Method** : `GET`

**Auth required** : YES

**Permissions required** : Authenticated User

#### Example:

http://localhost:5000/api/bank-accounts

#### Success Response

**Code** : `200 OK`

**Content examples**

```json
[
    {
        "name": "Plaid Saving",
        "institution_name": "Wells Fargo",
        "id": 1,
    },
    ...
]
```

#### Notes

- Get a list of bank accounts for all profiles related to employer or logged user 

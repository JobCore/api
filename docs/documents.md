# Documents

## Create a new Document

**URL** : `/api/document`

**Method** : `POST`

**Auth required** : YES

**Permissions required** : Authenticated User

## Request Params


| key                   | Example Value | Required?     |
| --------------------  | ------------  | ------------- |
| document              |       ""      |     Yes       |


## Example:

http://localhost:5000/api/document

## Success Response

**Code** : `200 OK`

**Content examples**


```json

```

## Notes

## List my documents

**URL** : `/api/document`

**Method** : `GET`

**Auth required** : YES

**Permissions required** : Authenticated User

## Example:

http://localhost:5000/api/document

## Success Response

**Code** : `200 OK`

**Content examples**


```json
[
    {
        "document":"URL to the document",
        "state": "The state",
        "id": 123,
        "rejected_reason": "Some reason"
    }
            ...
]
```

## Notes
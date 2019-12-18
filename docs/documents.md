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

Aqui esta la nueva version del api:

1. Para obtener todos los tipos de documentos de una lista:
```
GET /documents?type=<document_type>

Querystring:
    - type=identity,employment,form

```
2. Para obtener todos los documentos del employee que esta logeado:
```
GET /employee/me/documents?type=<document_type>&status=<document_status>&type_id=<specific_type_id>

Querystring:
    - type=identity,employment,form
    - status=PENDING,APPROVED,REJECTED
    - type_id=id del tipo, por ejemplo: 1,2,3,etc.

```

3. Para borrary un document
```
DELETE /employee/me/documents/id
```

4. Para obtener detalles de un documento
```
GET /employee/me/documents/id
```
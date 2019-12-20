# Documents

0. Crear un documento

POST /employee/me/documents

**Auth required** : YES

**Permissions required** : Authenticated User

**Parameters**:

| key                   | Example Value | Required?     |
| --------------------  | ------------  | ------------- |
| document              | <base64 data> | Yes           |
| document_type         | 1             | Yes           |



## Success Response

**Code** : `200 OK`


## Notes


1. Para obtener todos los tipos de documentos de una lista:

**URL** : `/documents?type=<document_type>`

**Method** : `GET`

**Auth required** : YES

**Permissions required** : Authenticated User

**Querystring**:
    - type=identity,employment,form


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


```
2. Para obtener todos los documentos del employee que esta logeado:
```
GET /employee/me/documents?type=<document_type>&status=<document_status>&type_id=<specific_type_id>

Querystring:
    - type=identity,employment,form
    - status=PENDING,APPROVED,REJECTED
    - type_id=id del tipo, por ejemplo: 1,2,3,etc.

```

3. Para borrar  un document
```
DELETE /employee/me/documents/id
```

4. Para obtener detalles de un documento
```
GET /employee/me/documents/id
```
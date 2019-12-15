
# Update Profile



PUT /api/profiles/me

### REQUEST

```
{
            'first_name': 'Angel',
            'last_name': 'Cerberus',
            'bio': 'Some BIO',
            "city": "Miami",
            "profile_city": <city_id>
        }
```

### Response

```
{"id":6,"user":{"first_name":"Angel","last_name":"Cerberus","email":"employee1@testdoma.in"},"picture":"https://scot...d_at":"2019-12-15T15:40:53.502453Z","status":"PENDING_EMAIL_VALIDATION","profile_city":7,"employer":null,"employee":6}
```
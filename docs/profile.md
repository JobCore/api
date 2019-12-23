
# Update Profile



## PUT /api/profiles/me

### REQUEST

```json
{
    "first_name": "Angel",
    "last_name": "Cerberus",
    "bio": "Some BIO",
    "city": "Miami",
    "profile_city": "<city_id>"
}
```

### Response

```json
{
    "id":6,
    "user":{
        "first_name":"Angel",
        "last_name":"Cerberus",
        "email":"employee1@testdoma.in"
    },
    "picture":"https://scot...d_at",
    "created_at": "2019-12-15T15:40:53.502453Z",
    "status":"PENDING_EMAIL_VALIDATION",
    "profile_city":7,
    "employer":null,
    "employee":6
}
```

## GET /api/profiles/me
```json
{
  "id": 2,
  "positions": [
    {
      "id": 1,
      "picture": "",
      "title": "Server",
      "description": "",
      "meta_description": "",
      "meta_keywords": "",
      "created_at": "2018-09-13T19:45:00Z",
      "updated_at": "2018-09-13T19:45:00Z"
    },
    {
      "id": 3,
      "picture": "",
      "title": "Floor Manager",
      "description": "",
      "meta_description": "",
      "meta_keywords": "",
      "created_at": "2018-09-13T19:45:00Z",
      "updated_at": "2018-09-13T19:45:00Z"
    }
  ],
  "badges": [
    {
      "title": "English Proficient",
      "id": 1
    },
    {
      "title": "Service Quality",
      "id": 2
    }
  ],
  "favoritelist_set": [
    {
      "id": 1,
      "title": "Preferred Employees",
      "created_at": "2018-09-13T19:45:00Z",
      "updated_at": "2018-09-13T19:45:00Z",
      "auto_accept_employees_on_this_list": true,
      "employer": 1,
      "employees": [
        3,
        2
      ]
    }
  ],
  "user": {
    "first_name": "John",
    "last_name": "Lennon",
    "email": "a+employee2@jobcore.co",
    "profile": {
      "picture": "",
      "bio": ""
    }
  },
  "response_time": 0,
  "minimum_hourly_rate": "8.0",
  "stop_receiving_invites": false,
  "rating": null,
  "total_ratings": 0,
  "total_pending_payments": 0,
  "maximum_job_distance_miles": 50,
  "job_count": 0,
  "created_at": "2018-09-13T19:45:00Z",
  "updated_at": "2019-12-18T18:24:31.768428Z",
  "employment_verification_status": "MISSING_DOCUMENTS",
  "filing_status": "SINGLE",
  "allowances": 0,
  "extra_withholding": 0.0
}
```
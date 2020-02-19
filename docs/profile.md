# Profile


## Update profile

**URL** : `/api/profiles/me`

**Method** : `PUT`

**Auth required** : Yes

**Permissions required** : Authenticated User

#### Request Params:

| key             | Example Value                                | Required?     | Observations         |
| --------------  | -------------------------------------------  | ------------- | -------------------- |
| picture         |  "https://res.cloudinary.com/profile2.png"   |     No        |                      |
| bio             |  "Hi, I'm a person who like sports"          |     No        |                      |
| show_tutorial   |  true                                        |     No        |                      |
| location        |  " ... "                                     |     No        |                      |
| street_address  |  " ... "                                     |     No        |                      |
| country         |  "United                                     |     No        |                      |
| city            |  "New York"                                  |     No        |                      |
| profile_city    |  5                                           |     No        |                      |
| state           |  "New York"                                  |     No        |                      |
| zip_code        |  "10020"                                     |     No        |                      |
| latitude        |  40.7595055                                  |     No        |                      |
| longitude       |  -73.9828761                                 |     No        |                      |
| birth_date      |  "1990-05-21"                                |     No        |                      |
| phone_number    |  "+1-202-555-0139"                           |     No        |                      |
| last_4dig_ssn   |  "1234"                                      |     No        |                      |

#### Example

http://localhost:5000/api/profiles/me

#### Success Response

**Code** : `200 OK`

**Content examples**

```json
{
    "id":6,
    "user":{
        "first_name":"Angel",
        "last_name":"Cerberus",
        "email":"employee1@testdoma.in"
    },
    "picture":"https://scot...d_at",
    "bio": "",
    "show_tutorial": true,
    "location": "",
    "street_address": "",
    "country": "",
    "city": "New York",
    "state": "",
    "zip_code": null,
    "latitude": "0.00000000000",
    "longitude": "0.00000000000",
    "birth_date": "1990-05-03",
    "phone_number": "",
    "last_4dig_ssn": "1234",
    "employer_role": "ADMIN",
    "created_at": "2019-12-15T15:40:53.502453Z",
    "updated_at": "2019-12-15T15:40:53.502453Z",
    "status":"PENDING_EMAIL_VALIDATION",
    "profile_city":7,
    "employer":null,
    "employee":6
}
```


## Get profile

**URL** : `/api/profiles/me`

**Method** : `GET`

**Auth required** : Yes

**Permissions required** : Authenticated User

#### Example

http://localhost:5000/api/profiles/me

#### Success Response

**Code** : `200 OK`

**Content examples**

```json
{
  "id": 2,
  "user": {
    "first_name": "John",
    "last_name": "Lennon",
    "email": "a+employee2@jobcore.co",
  },
  "picture": "https://res.cloudinary.com/...",
  "bio": "",
  "location": "",
  "street_address": "",
  "country": "",
  "city": "",
  "state": "",
  "zip_code": null,
  "show_tutorial": true,,
  "latitude": "0.00000000000",
  "longitude": "0.00000000000",
  "birth_date": "1990-05-03",
  "phone_number": "",
  "last_4dig_ssn": "1234",
  "employer_role": "ADMIN",
  "profile_city": null  
  "status": "PENDING_EMAIL_VALIDATION",
  "created_at": "2018-09-13T19:45:00Z",
  "updated_at": "2019-12-18T18:24:31.768428Z",
  "employee":
    {
      "id": 2,
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
      "total_invites": 0,
      "employment_verification_status": "MISSING_DOCUMENTS",
      "filing_status": "SINGLE",
      "allowances": 0,
      "extra_withholding": 0.0
      "user":  2,
      "positions": [1, 2, 3, 4, 5],
      "badges": [
        {
          "title": "English Proficient",
          "id": 1,
          "image_url": " ... "
        },
        {
          "title": "Service Quality",
          "id": 2
          "image_url": " ... ",
        }
      ]
    },
  "employer": null
}
```

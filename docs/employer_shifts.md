# Shifts related to Employer

## Get a list of shifts related to current Employer

**URL** : `/api/employers/me/shifts`

**Method** : `GET`

**Auth required** : Yes

**Permissions required** : Authenticated User, User should be an Employer

#### Request Params:

| key            | Example Value        | Required?     | Observations                                                 |
| -------------  | -------------------  | ------------- | ------------------------------------------------------------ |
| status         |  OPEN,DRAFT          |   No          | OPEN, FILLED, PAUSED, EXPIRED, COMPLETED, DRAFT, CANCELLED   |
| filled         |  true                |   No          | true or anything                                             |
| not_status     |  EXPIRED (one value) |   No          | OPEN, FILLED, PAUSED, EXPIRED, COMPLETED, DRAFT, CANCELLED   |
| upcoming       |  true                |   No          | true or anything                                             |
| start          |  2020-01-05          |   No          |                                                              |
| end            |  2020-01-12          |   No          |                                                              |
| unrated        |  true                |   No          | true or anything                                             |
| employee_not   |  2,4,5               |   No          | list of ids, separated by comma                              |
| employee       |  2,4,5               |   No          | list of ids, separated by comma                              |
| candidate_not  |  3,6                 |   No          | list of ids, separated by comma                              |
| serializer     |  big                 |   No          | big or anything                                              |

Note: parameters listed in order of precedence

#### Example

http://localhost:5000/api/employers/me/shifts?not_status=expired&start=2020-01-01

#### Success Response

**Code** : `200 OK`

**Content examples**

```json
[
  {
    "id": 3,
    "venue":
      {
        "title": "The Miller Plantation",
        "id": 2,
        "latitude": "25.744526",
        "longitude": "-80.260033",
        "street_address": "Coral Gables",
        "zip_code": null
      },
    "position":
      {
        "title": "Floor Manager",
        "id": 3
      },
    "maximum_allowed_employees": 2,
    "minimum_hourly_rate": "15.0",
    "status": "OPEN",
    "starting_at": "2020-10-09T19:45:00Z",
    "ending_at": "2020-10-10T02:45:00Z",
    "created_at": "2018-08-13T19:45:00Z",
    "employer": 1,
    "author": null,
    "candidates": [
      3,
      4,
      5,
      6
    ],
    "employees": []
  },
  {
    "id": 4,
    "venue":
      {
        "title": "The Club of Knights",
        "id": 1,
        "latitude": "25.744526",
        "longitude": "-80.260033",
        "street_address": "270 Catalonia, Coral Gables",
        "zip_code": null
      },
    "position":
      {
        "title": "Server",
        "id": 1
      },
    "maximum_allowed_employees": 1,
    "minimum_hourly_rate": "15.0",
    "status": "OPEN",
    "starting_at": "2019-09-09T19:45:00Z",
    "ending_at": "2019-09-10T02:45:00Z",
    "created_at": "2018-08-13T19:45:00Z",
    "employer": 1,
    "author": null,
    "candidates": [],
    "employees": [
      3
    ]
  },
  ...
]
```

or the following when **serializer=big** is provided
```json
[
  {
    "id": 4,
    "venue":
      {
        "title": "The Club of Knights",
        "id": 1,
        "latitude": "25.744526",
        "longitude": "-80.260033",
        "street_address": "270 Catalonia, Coral Gables",
        "zip_code": null
      },
    "position":
      {
        "title": "Server",
        "id": 1
      },
    "employees": [
      {
        "user": {
          "first_name": "Paul",
          "last_name": "McCartney",
          "profile": {
            "picture": ""
          }
        },
        "id": 3
      }
    ],
    "maximum_allowed_employees": 1,
    "minimum_hourly_rate": "15.0",
    "status": "OPEN",
    "starting_at": "2019-09-09T19:45:00Z",
    "ending_at": "2019-09-10T02:45:00Z",
    "created_at": "2018-08-13T19:45:00Z",
    "maximum_clockin_delta_minutes": 15,
    "maximum_clockout_delay_minutes": 15,
    "employer": 1,
    "author": null,
    "candidates": []
  },
  ...
]
```

#### Notes

- Status values can be uppercase or lowercase.
- If `status` parameter is not provided, shifts with CANCELLED status are not returned.
- `filled` parameter with `true` value is equal to use `status` parameter with `filled` value


## Get data of shift related to current Employer

**URL** : `/api/employers/me/shifts/<id>`

**Method** : `GET`

**Auth required** : Yes

**Permissions required** : Authenticated User, User should be an Employer

#### Request Params:

Any

#### Example

http://localhost:5000/api/employers/me/shifts/4

#### Success Response

**Code** : `200 OK`

**Content examples**

```json
{
  "id": 4,
  "venue":
    {
      "title": "The Club of Knights",
      "id": 1,
      "latitude": "25.744526",
      "longitude": "-80.260033",
      "street_address": "270 Catalonia, Coral Gables",
      "zip_code": null
    },
  "position": {
    "title": "Server",
    "id": 1
  },
  "candidates": [],
  "employees": [
    {
      "user": {
        "first_name": "Paul",
        "last_name": "McCartney",
        "profile": {
          "picture": ""
        }
      },
      "id": 3,
      "badges": [
        3,
        4
      ],
      "positions": [],
      "favoritelist_set": [
        {
          "id": 1,
          "title": "Preferred Employees",
          "employer": 1
        },
        {
          "id": 2,
          "title": "Preferred Employees",
          "employer": 1
        }
      ]
    }
  ],
  "employer": {
    "title": "Fetes and Events",
    "id": 1,
    "picture": "",
    "rating": "0.0",
    "total_ratings": 0
  },
  "required_badges": [],
  "allowed_from_list": [],
  "application_restriction": "ANYONE",
  "maximum_allowed_employees": 1,
  "minimum_hourly_rate": "15.0",
  "minimum_allowed_rating": "0.0",
  "status": "OPEN",
  "starting_at": "2019-09-09T19:45:00Z",
  "ending_at": "2019-09-10T02:45:00Z",
  "rating": "0.0",
  "created_at": "2018-08-13T19:45:00Z",
  "updated_at": "2018-08-13T19:45:00Z",
  "maximum_clockin_delta_minutes": 15,
  "maximum_clockout_delay_minutes": 15,
  "author": null
}
```

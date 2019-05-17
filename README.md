# Job API Client
[![buddy pipeline](https://app.buddy.works/jobcore/rest-api/pipelines/pipeline/132168/badge.svg?token=d248fd7fd9018672bfcfc67ebc25c73faf27f90b18b94d15856cdea170fb18be "buddy pipeline")](https://app.buddy.works/jobcore/rest-api/pipelines/pipeline/132168) <img src="./coverage.svg" alt="coverage svg">

## Requirements

1. Python 3
2. PIP package manager
3. Postgree

## Installation

- Install `virtualenv` on your machine

```bash
$ pip3 install virtualenv
```
* CD into the cloned repository and run:
```bash
$ virtualenv venv
```

- Activate environment on Windows and install packages
Activete venv on windows: `$ venv\Scripts\activate.bat`
Activate venv Linux/MacOS `$ source venv/bin/activate`
To deactivate use `deactivate`

- Install required packages
```bash
$ pip3 install -r requirements.txt
```

- Copy and rename `jobcore/.env.example` to `jobcore/.env` and set environment variables
- Generate a new Secret Key `$ python3 keygen_django.py` or `$ openssl rand -base64 32`

Run migrations: `$ python manage.py migrate`

Run django: `$ python manage.py runserver $IP:$PORT`

### Lod fixtures (if needed)
```python
python manage.py loaddata api/fixtures/*.yaml
```

### Run tests
```
python manage.py test api
```

Note: If you are running the old tests:

- For a particular test: `pytest api/tests/test_invites.py`
- For all tests: `pytest`

### Extra useful stuff

Find static files:
```
python manage.py findstatic --verbosity 2 social-media/facebook.png
```

### Packages i don;t know if I should install
```
distribute==0.6.27
poster==0.8.1
wsgiref==0.1.2
```


## Heroku

### Adding public keys to heroku
heroku keys:add ~/.ssh/path/to/public/key

### Heroku config vars
heroku config:set GITHUB_USERNAME=joesmith

### Start python shell
heroku run python manage.py shell

### Deploy
git push heroku master

## add remote
heroku git:remote -a
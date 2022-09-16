# Job API Client

[![buddy pipeline](https://app.buddy.works/jobcore/rest-api/pipelines/pipeline/132168/badge.svg?token=d248fd7fd9018672bfcfc67ebc25c73faf27f90b18b94d15856cdea170fb18be "buddy pipeline")](https://app.buddy.works/jobcore/rest-api/pipelines/pipeline/132168) <img src="./coverage.svg" alt="coverage svg">

## Requirements

1. Python 3.7.4
2. Pipenv
3. Postgree

## Installation

- Install required packages

```bash
$ pipenv install
```

- Create database (if needed):

```
psql -U gitpod -c 'DROP DATABASE jobcore;'
psql -U gitpod -c 'CREATE DATABASE jobcore;'
psql -U gitpod -c 'CREATE EXTENSION unaccent;' -d jobcore
```

- Copy and rename `jobcore/.env.example` to `jobcore/.env` and set environment variables
- Generate a new Secret Key `$ pipenv run genkey` or `$ openssl rand -base64 32`

Run migrations: `$ pipenv run migrate`

Run django: `$ pipenv run start`

### Lod fixtures (if needed)

```sh
$ python3 manage.py reset
$ pipenv run seed [development|production]
```

### Run tests

```sh
$ pipenv run tests
```

Note: If you are running a particular test:

- For a particular test: `pytest api/tests/test_invites.py`

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
heroku git:remote -a jobcore


## Postgres docker

## Postgres
### Build
docker build -t jobcore/bd -f ./DockerfileForPostgres .
### Run
docker run -it -p 5432:5432 -h localhost --ip 127.0.0.1 jobcore/bd


## Django App
### Build
docker build -t jobcore/app -f ./DockerfileForLiveReloadApp  .
### Run (pwd: fish shell variable pwd)
docker run -it -p 5000:5000 -v (pwd):/app jobcore/app


## Restoring a postgree dump
psql -U gitpod -c 'DROP DATABASE jobcore;';
psql -U gitpod -c 'CREATE DATABASE jobcore;';
psql -U gitpod -c 'CREATE EXTENSION unaccent;' -d jobcore;
psql -U gitpod -c 'CREATE ROLE <role_name> WITH SUPERUSER';
pg_restore -c -d jobcore [dumpfile_name]

## CREATING AN ADMIN usER 
pipenv shell createsuperuser
now enter username and password.

# Job API Client
[![buddy pipeline](https://app.buddy.works/jobcore/rest-api/pipelines/pipeline/132168/badge.svg?token=d248fd7fd9018672bfcfc67ebc25c73faf27f90b18b94d15856cdea170fb18be "buddy pipeline")](https://app.buddy.works/jobcore/rest-api/pipelines/pipeline/132168) <img src="./coverage.svg" alt="coverage svg">

## Requirements

1. Python 3
2. PIP package manager

## Quick commands

1. Run mysql:

    ```bash
    $ mysql-ctl start
    ```

2. Create a virtual environment

    * Install `virtualenv` on your machine

    ```bash
    $ pip install virtualenv
    ```

    * CD into the cloned repository and run:

    ```bash
    $ virtualenv venv
    ```

    - Activate environment on Windows and install packages

    ```bash
    $ venv\Scripts\activate.bat
    ```

    - Activate environment on Linux/MacOS and install packages

    ```bash
    $ source venv/bin/activate
    ```

    - To deactivate use `deactivate`

3. Install required packages

    ```bash
    $ pip install -r requirements.txt
    ```

4. Copy and rename **jobcore/.env.example** to **jobcore/.env** and set environment variables

    * Generate a new Secret Key

    ```bash
    $ python keygen_django.py
    ```

    or

    ```
    $ openssl rand -base64 32
    ```

5. Run migrations

    ```bash
    $ python manage.py migrate
    ```

6. Run django:

    ```bash
    $ python manage.py runserver $IP:$PORT
    ```
    
### Extra useful stuff

Find static files:
```
python manage.py findstatic --verbosity 2 social-media/facebook.png
```

### Adding public keys to heroku
heroku keys:add ~/.ssh/path/to/public/key

## Heroku config vars
heroku config:set GITHUB_USERNAME=joesmith

## Start python shell
heroku run python manage.py shell

## Deploy
git push heroku master
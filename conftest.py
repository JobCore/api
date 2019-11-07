import pytest, os, dj_database_url
TEST_DATABASE_URL = os.environ.get('TEST_DATABASE_URL')

@pytest.fixture(scope='session')
def django_db_setup():
    from django.conf import settings
    settings.DATABASES['default'] = dj_database_url.config(default=TEST_DATABASE_URL)
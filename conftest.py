#import pytest, os, dj_database_url
# 'default': dj_database_url.config(default="sqlite3:///tests.sqlite3")
# tests="pytest --color=yes --cov --cov-report=html --reuse-db --ds=jobcore.settings"

import os
import pytest
import dj_database_url

@pytest.fixture(scope='session')
def django_db_modify_db_settings(request):
    from jobcore import settings
    settings.DATABASES['default'] = {
        'ENGINE':'django.db.backends.sqlite3',
        'TEST': 'test.sqlite3',
        'NAME': 'test.sqlite3'
    }
    #print("pipo"+str(settings.DATABASES['default']))
    #exit()
import pytest, dj_database_url
from django.db import connections

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


def run_sql(sql):
    conn = psycopg2.connect(database='postgres')
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    cur.execute(sql)
    conn.close()


@pytest.yield_fixture(scope='session')
def django_db_setup():
    from django.conf import settings

    settings.DATABASES['default'] = dj_database_url.config(env='TEST_DATABASE_URL')

    run_sql('DROP SCHEMA public CASCADE')
    run_sql('CREATE SCHEMA public')

    yield

    for connection in connections.all():
        connection.close()


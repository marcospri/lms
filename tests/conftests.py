import functools
import os
from unittest import mock

import pytest
import sqlalchemy
from sqlalchemy.orm import sessionmaker

from lms import db

__all__ = [
    "patch",
    "db_session",
    "db_engine",
    "SESSION",
    "TEST_DATABASE_URL",
    "TEST_SETTINGS",
]

SESSION = sessionmaker()
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql://postgres@localhost:5433/lms_test"
)

# Settings that will end up in pyramid_request.registry.settings.
TEST_SETTINGS = {
    "sqlalchemy.url": TEST_DATABASE_URL,
    "via_url": "http://TEST_VIA_SERVER.is/",
    "jwt_secret": "test_secret",
    "google_client_id": "fake_client_id",
    "google_developer_key": "fake_developer_key",
    "google_app_id": "fake_app_id",
    "lms_secret": "TEST_LMS_SECRET",
    "hashed_pw": "e46df2a5b4d50e259b5154b190529483a5f8b7aaaa22a50447e377d33792577a",
    "salt": "fbe82ee0da72b77b",
    "username": "report_viewer",
    "aes_secret": b"TSeQ7E3dzbHgu5ydX2xCrKJiXTmfJbOe",
    "jinja2.filters": {
        "static_path": "pyramid_jinja2.filters:static_path_filter",
        "static_url": "pyramid_jinja2.filters:static_url_filter",
    },
    "h_client_id": "TEST_CLIENT_ID",
    "h_client_secret": "TEST_CLIENT_SECRET",
    "h_jwt_client_id": "TEST_JWT_CLIENT_ID",
    "h_jwt_client_secret": "TEST_JWT_CLIENT_SECRET",
    "h_authority": "TEST_AUTHORITY",
    "h_api_url_public": "https://example.com/api/",
    "h_api_url_private": "https://private.com/api/",
    "rpc_allowed_origins": ["http://localhost:5000"],
    "oauth2_state_secret": "test_oauth2_state_secret",
}


@pytest.fixture(scope="session")
def db_engine():
    engine = sqlalchemy.create_engine(TEST_DATABASE_URL)
    db.init(engine)
    return engine


@pytest.yield_fixture
def db_session(db_engine):
    """
    Yield the SQLAlchemy session object.

    We enable fast repeatable database tests by setting up the database only
    once per session (see :func:`db_engine`) and then wrapping each test
    function in a transaction that is rolled back.

    Additionally, we set a SAVEPOINT before entering the test, and if we
    detect that the test has committed (i.e. released the savepoint) we
    immediately open another. This has the effect of preventing test code from
    committing the outer transaction.

    """
    conn = db_engine.connect()
    trans = conn.begin()
    session = SESSION(bind=conn)
    session.begin_nested()

    @sqlalchemy.event.listens_for(session, "after_transaction_end")
    def restart_savepoint(session, transaction):  # pylint:disable=unused-variable
        if (
            transaction.nested and not transaction._parent.nested
        ):  # pylint:disable=protected-access
            session.begin_nested()

    try:
        yield session
    finally:
        session.close()
        trans.rollback()
        conn.close()


def autopatcher(request, target, **kwargs):
    """Patch and cleanup automatically. Wraps :py:func:`mock.patch`."""
    options = {"autospec": True}
    options.update(kwargs)
    patcher = mock.patch(target, **options)
    obj = patcher.start()
    request.addfinalizer(patcher.stop)
    return obj


@pytest.fixture
def patch(request):
    return functools.partial(autopatcher, request)

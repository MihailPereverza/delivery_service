import os
import tempfile

import pytest
from data.db_session import global_init
from app import app


@pytest.fixture
def client():
    with app.test_client() as client:
        with app.app_context():
            global_init('tmp/test.db')
        yield client


def test_empty_db(client):
    """Start with a blank database."""

    rv = client.get('/')
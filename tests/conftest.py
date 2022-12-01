import pytest


@pytest.fixture()
def client():
    from main import app
    app.config['TESTING'] = True
    return app.test_client()

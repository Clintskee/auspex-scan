"""Shared Django test configuration."""

import pytest
from rest_framework.test import APIClient


@pytest.fixture(autouse=True)
def database_access(db):
    """Give API tests access to pytest-django's isolated database."""


@pytest.fixture
def api_client():
    return APIClient()

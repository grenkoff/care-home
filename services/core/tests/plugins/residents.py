"""Fixtures of the tests of residents."""

import datetime as dt

import pytest

from server.apps.accounts.models import User
from server.apps.residents.models import Resident


@pytest.fixture
def resident() -> Resident:
    """Resident who lives in the home."""
    return Resident.objects.create(
        full_name='Maria Ivanova',
        moved_in_on=dt.date(2026, 1, 10),
    )


@pytest.fixture
def relative() -> User:
    """Relative of residents with an account."""
    return User.objects.create_user(username='anna@example.test')

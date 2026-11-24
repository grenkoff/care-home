"""Fixtures of the tests of accounts."""

import hashlib
from datetime import timedelta
from typing import Final

import pytest
from django.utils import timezone

from server.apps.accounts.models import Invitation

_CODE: Final = 'code-of-anna'


@pytest.fixture
def invitation() -> Invitation:
    """Invitation of Anna that works for one more day."""
    return Invitation.objects.create(
        email='anna@example.test',
        digest=hashlib.sha256(_CODE.encode()).hexdigest(),
        expires_at=timezone.now() + timedelta(days=1),
    )


@pytest.fixture
def invitation_page() -> str:
    """Address of the page that the link of Anna opens, in English."""
    return f'/en/invitation/{_CODE}/'

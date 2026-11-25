"""Fixtures of the tests of accounts."""

import hashlib
import re
from datetime import timedelta
from http import HTTPStatus
from typing import Final

import pytest
from django.test import Client
from django.utils import timezone

from server.apps.accounts.models import Authenticator, Invitation, User

_CODE: Final = 'code-of-anna'
_EMAIL: Final = 'anna@example.test'
_CHOSEN: Final = 'a long secret'
_KEY: Final = 'GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ'


@pytest.fixture
def invitation() -> Invitation:
    """Invitation of Anna that works for one more day."""
    return Invitation.objects.create(
        email=_EMAIL,
        digest=hashlib.sha256(_CODE.encode()).hexdigest(),
        expires_at=timezone.now() + timedelta(days=1),
    )


@pytest.fixture
def invitation_page() -> str:
    """Address of the page that the link of Anna opens, in English."""
    return f'/en/invitation/{_CODE}/'


@pytest.fixture
def pending(client: Client) -> Client:
    """Client of a relative without an authenticator who gave the password."""
    User.objects.create_user(username=_EMAIL, email=_EMAIL, password=_CHOSEN)
    client.post('/en/sign-in/', {'username': _EMAIL, 'password': _CHOSEN})
    return client


@pytest.fixture
def shown_key(pending: Client) -> str:
    """Key that the page of connecting an authenticator app shows."""
    page = pending.get('/en/second-factor/connect/')
    assert page.status_code == HTTPStatus.OK
    found = re.search(r'secret=([A-Z2-7]+)', page.content.decode())
    assert found
    return found[1]


@pytest.fixture
def connected_key(pending: Client) -> str:
    """Key of the authenticator app that the relative connected earlier."""
    Authenticator.objects.create(
        user=User.objects.get(username=_EMAIL),
        key=_KEY,
        used_step=0,
    )
    return _KEY

"""Tests of the admin where staff invite relatives."""

import hashlib
import re
from datetime import timedelta
from typing import Final

import pytest
from django.conf import LazySettings
from django.test import Client
from django.utils import timezone

from server.apps.accounts.models import Invitation

_ADD: Final = '/admin/accounts/invitation/add/'
_LINK: Final = re.compile(r'http://testserver/ru/invitation/([\w-]+)/')


def _invited(admin_client: Client) -> str:
    """Invites a relative and returns the page staff see next."""
    return admin_client.post(
        _ADD,
        {'email': 'anna@example.test'},
        follow=True,
    ).content.decode()


@pytest.mark.django_db
def test_staff_see_the_link_to_send(admin_client: Client) -> None:
    assert len(_LINK.findall(_invited(admin_client))) == 1


@pytest.mark.django_db
def test_site_keeps_only_a_digest_of_the_link(admin_client: Client) -> None:
    codes = _LINK.findall(_invited(admin_client))
    digests = [hashlib.sha256(code.encode()).hexdigest() for code in codes]

    assert digests == list(Invitation.objects.values_list('digest', flat=True))


@pytest.mark.django_db
def test_link_is_shown_only_once(admin_client: Client) -> None:
    _invited(admin_client)

    page = admin_client.get('/admin/accounts/invitation/').content.decode()

    assert not _LINK.findall(page)


@pytest.mark.django_db
def test_link_expires_after_the_days_of_settings(
    admin_client: Client,
    settings: LazySettings,
) -> None:
    settings.INVITATION_DAYS = 3
    before = timezone.now()

    _invited(admin_client)

    after = timezone.now()
    assert [
        before + timedelta(days=3) <= expiry <= after + timedelta(days=3)
        for expiry in Invitation.objects.values_list('expires_at', flat=True)
    ] == [True]

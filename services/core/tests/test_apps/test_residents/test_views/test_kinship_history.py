"""Tests of the history of links, which staff revoke but never rewrite."""

import datetime as dt
from http import HTTPStatus
from typing import Final

import pytest
from django.contrib.auth.models import Permission
from django.test import Client
from django.utils import timezone

from server.apps.accounts.models import User
from server.apps.residents.models import Kinship

_LIST: Final = '/admin/residents/kinship/'


def _revoke(client: Client, kinship: Kinship) -> None:
    """Runs the admin action that revokes the link."""
    client.post(_LIST, {'action': 'revoke', '_selected_action': [str(kinship.pk)]})


@pytest.mark.django_db
def test_staff_revoke_a_link(admin_client: Client, kinship: Kinship) -> None:
    _revoke(admin_client, kinship)

    kinship.refresh_from_db()
    assert kinship.revoked_at is not None


@pytest.mark.django_db
def test_staff_who_only_view_links_cannot_revoke(
    client: Client,
    kinship: Kinship,
) -> None:
    viewer = User.objects.create_user(username='viewer@example.test', is_staff=True)
    viewer.user_permissions.add(Permission.objects.get(codename='view_kinship'))
    client.force_login(viewer)

    _revoke(client, kinship)

    kinship.refresh_from_db()
    assert kinship.revoked_at is None


@pytest.mark.django_db
def test_revoking_again_keeps_the_first_time(
    admin_client: Client,
    kinship: Kinship,
) -> None:
    first = timezone.now() - dt.timedelta(days=1)
    Kinship.objects.filter(pk=kinship.pk).update(revoked_at=first)

    _revoke(admin_client, kinship)

    kinship.refresh_from_db()
    assert kinship.revoked_at == first


@pytest.mark.django_db
def test_staff_cannot_change_a_link(admin_client: Client, kinship: Kinship) -> None:
    admin_client.post(
        f'{_LIST}{kinship.pk}/change/',
        {'resident': kinship.resident_id, 'kind': 'spouse'},
    )

    kinship.refresh_from_db()
    assert kinship.kind == 'child'


@pytest.mark.django_db
def test_staff_cannot_delete_a_link(admin_client: Client, kinship: Kinship) -> None:
    response = admin_client.get(f'{_LIST}{kinship.pk}/delete/')

    assert response.status_code == HTTPStatus.FORBIDDEN

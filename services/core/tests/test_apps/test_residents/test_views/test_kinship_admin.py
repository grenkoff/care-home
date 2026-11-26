"""Tests of the admin where staff link residents to their relatives."""

from http import HTTPStatus
from typing import Final

import pytest
from django.test import Client

from server.apps.accounts.models import User
from server.apps.residents.models import Kinship, Resident

_ADD: Final = '/admin/residents/kinship/add/'
_LIST: Final = '/admin/residents/kinship/'
_CHILD: Final = 'child'


@pytest.mark.django_db
def test_staff_link_a_relative_by_email(
    admin_client: Client,
    admin_user: User,
    resident: Resident,
) -> None:
    anna = User.objects.create_user(username='anna@example.test')

    admin_client.post(
        _ADD,
        {'resident': resident.pk, 'kind': _CHILD, 'relative': 'Anna@Example.test'},
    )

    assert list(
        Kinship.objects.values_list('resident', 'kind', 'relative', 'granted_by'),
    ) == [(resident.pk, _CHILD, anna.pk, admin_user.pk)]


@pytest.mark.django_db
def test_refuses_an_email_without_an_account(
    admin_client: Client,
    resident: Resident,
) -> None:
    response = admin_client.post(
        _ADD,
        {'resident': resident.pk, 'kind': _CHILD, 'relative': 'boris@example.test'},
        headers={'Accept-Language': 'en'},
    )

    assert 'No account has this e-mail' in response.content.decode()
    assert not Kinship.objects.exists()


@pytest.mark.django_db
def test_staff_revoke_a_link(
    admin_client: Client,
    admin_user: User,
    resident: Resident,
) -> None:
    kinship = Kinship.objects.create(
        resident=resident,
        kind=_CHILD,
        relative=admin_user.pk,
        granted_by=admin_user.pk,
    )

    admin_client.post(
        _LIST,
        {'action': 'revoke', '_selected_action': [str(kinship.pk)]},
    )

    kinship.refresh_from_db()
    assert kinship.revoked_at is not None


@pytest.mark.django_db
def test_staff_cannot_delete_a_link(
    admin_client: Client,
    admin_user: User,
    resident: Resident,
) -> None:
    kinship = Kinship.objects.create(
        resident=resident,
        kind=_CHILD,
        relative=admin_user.pk,
        granted_by=admin_user.pk,
    )

    response = admin_client.get(f'{_LIST}{kinship.pk}/delete/')

    assert response.status_code == HTTPStatus.FORBIDDEN

"""Tests of the admin where staff link residents to their relatives."""

import uuid
from http import HTTPStatus
from typing import Final

import pytest
from django.test import Client

from server.apps.accounts.models import User
from server.apps.residents.models import Kinship, Resident

_ADD: Final = '/admin/residents/kinship/add/'
_CHILD: Final = 'child'


def _granted(resident: uuid.UUID, email: str) -> dict[str, object]:
    """Fields of the form that grants a link, as staff fill them in."""
    return {'resident': resident, 'kind': _CHILD, 'relative': email}


@pytest.mark.django_db
def test_staff_link_a_relative_by_email(
    admin_client: Client,
    admin_user: User,
    resident: Resident,
    relative: User,
) -> None:
    admin_client.post(_ADD, _granted(resident.pk, 'Anna@Example.test'))

    assert list(
        Kinship.objects.values_list('resident', 'kind', 'relative', 'granted_by'),
    ) == [(resident.pk, _CHILD, relative.pk, admin_user.pk)]


@pytest.mark.django_db
def test_refuses_an_email_without_an_account(
    admin_client: Client,
    resident: Resident,
) -> None:
    response = admin_client.post(
        _ADD,
        _granted(resident.pk, 'boris@example.test'),
        headers={'Accept-Language': 'en'},
    )

    assert 'No account has this e-mail' in response.content.decode()
    assert not Kinship.objects.exists()


@pytest.mark.django_db
def test_refuses_an_account_not_copied_yet(
    admin_client: Client,
    resident: Resident,
) -> None:
    User.objects.create_user(username='boris@example.test')

    admin_client.post(_ADD, _granted(resident.pk, 'boris@example.test'))

    assert not Kinship.objects.exists()


@pytest.mark.django_db
def test_refuses_a_second_working_link(
    admin_client: Client,
    kinship: Kinship,
    relative: User,
) -> None:
    response = admin_client.post(
        _ADD,
        _granted(kinship.resident_id, relative.username),
    )

    assert (response.status_code, Kinship.objects.count()) == (HTTPStatus.OK, 1)

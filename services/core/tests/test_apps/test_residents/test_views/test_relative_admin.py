"""Tests of the admin where staff see the accounts that residents copied."""

from http import HTTPStatus
from typing import Final

import pytest
from django.test import Client

from server.apps.accounts.models import User
from server.apps.residents.models import Relative

_LIST: Final = '/admin/residents/relative/'


@pytest.mark.django_db
@pytest.mark.usefixtures('relative')
def test_staff_see_the_copied_relatives(admin_client: Client) -> None:
    assert 'anna@example.test' in admin_client.get(_LIST).content.decode()


@pytest.mark.django_db
def test_staff_cannot_add_a_relative(admin_client: Client) -> None:
    response = admin_client.get(f'{_LIST}add/')

    assert response.status_code == HTTPStatus.FORBIDDEN


@pytest.mark.django_db
def test_staff_cannot_change_a_relative(admin_client: Client, relative: User) -> None:
    copied = Relative.objects.get(account=relative.pk)

    response = admin_client.post(f'{_LIST}{copied.pk}/change/', {})

    assert response.status_code == HTTPStatus.FORBIDDEN


@pytest.mark.django_db
def test_staff_cannot_delete_a_relative(admin_client: Client, relative: User) -> None:
    copied = Relative.objects.get(account=relative.pk)

    response = admin_client.get(f'{_LIST}{copied.pk}/delete/')

    assert response.status_code == HTTPStatus.FORBIDDEN

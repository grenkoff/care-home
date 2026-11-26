"""Tests of the page where an admitted relative sees the cameras of the home."""

import datetime as dt
from http import HTTPStatus
from typing import Final

import pytest
from django.test import Client

from server.apps.accounts.models import User
from server.apps.cameras.models import Camera
from server.apps.residents.models import Resident

_PAGE: Final = '/en/cameras/'


@pytest.mark.django_db
@pytest.mark.usefixtures('kinship', 'camera')
def test_relative_sees_the_active_cameras(client: Client, relative: User) -> None:
    client.force_login(relative)

    assert 'Garden' in client.get(_PAGE).content.decode()


@pytest.mark.django_db
@pytest.mark.usefixtures('kinship')
def test_hides_the_cameras_that_are_off(client: Client, relative: User) -> None:
    Camera.objects.create(name_ru='Холл', name_en='Hall', stream='hall', active=False)
    client.force_login(relative)

    assert 'Hall' not in client.get(_PAGE).content.decode()


@pytest.mark.django_db
@pytest.mark.usefixtures('kinship', 'camera')
def test_names_the_cameras_in_russian(client: Client, relative: User) -> None:
    client.force_login(relative)

    assert 'Сад' in client.get('/ru/cameras/').content.decode()


@pytest.mark.django_db
@pytest.mark.usefixtures('kinship', 'camera')
def test_refuses_a_stranger(client: Client) -> None:
    client.force_login(User.objects.create_user(username='boris@example.test'))

    assert client.get(_PAGE).status_code == HTTPStatus.FORBIDDEN


@pytest.mark.django_db
@pytest.mark.usefixtures('kinship')
def test_refuses_once_the_resident_moved_out(
    client: Client,
    relative: User,
    resident: Resident,
) -> None:
    Resident.objects.filter(pk=resident.pk).update(moved_out_on=dt.date(2026, 3, 1))
    client.force_login(relative)

    assert client.get(_PAGE).status_code == HTTPStatus.FORBIDDEN


@pytest.mark.django_db
def test_sends_a_visitor_to_sign_in(client: Client) -> None:
    response = client.get(_PAGE)

    assert (response.status_code, response.headers.get('Location')) == (
        HTTPStatus.FOUND,
        '/en/sign-in/?next=/en/cameras/',
    )


@pytest.mark.django_db
@pytest.mark.usefixtures('kinship')
def test_cameras_are_never_cached(client: Client, relative: User) -> None:
    client.force_login(relative)

    response = client.get(_PAGE)

    assert 'no-store' in response.headers.get('Cache-Control', '')

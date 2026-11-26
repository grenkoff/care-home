"""Tests of the page of one camera, which records every viewing."""

from http import HTTPStatus

import pytest
from django.test import Client

from server.apps.accounts.models import User
from server.apps.cameras.models import Camera, Viewing


@pytest.mark.django_db
def test_the_list_leads_to_the_camera(watcher: Client, camera_page: str) -> None:
    assert f'href="{camera_page}"' in watcher.get('/en/cameras/').content.decode()


@pytest.mark.django_db
@pytest.mark.parametrize(
    ('language', 'shown'),
    [('en', 'Garden'), ('ru', 'Сад'), ('ru', 'Все камеры')],
)
def test_relative_sees_the_camera(
    watcher: Client,
    camera_page: str,
    language: str,
    shown: str,
) -> None:
    page = camera_page.replace('/en/', f'/{language}/')

    assert shown in watcher.get(page).content.decode()


@pytest.mark.django_db
def test_records_who_opened_the_camera(
    watcher: Client,
    camera_page: str,
    camera: Camera,
    relative: User,
) -> None:
    watcher.get(camera_page)

    assert list(Viewing.objects.values_list('viewer', 'camera')) == [
        (relative.pk, camera.pk),
    ]


@pytest.mark.django_db
def test_a_camera_that_is_off_is_not_found(
    watcher: Client,
    camera_page: str,
    camera: Camera,
) -> None:
    Camera.objects.filter(pk=camera.pk).update(active=False)

    response = watcher.get(camera_page)

    assert (response.status_code, Viewing.objects.count()) == (
        HTTPStatus.NOT_FOUND,
        0,
    )


@pytest.mark.django_db
@pytest.mark.usefixtures('kinship')
def test_refuses_a_stranger(client: Client, camera_page: str) -> None:
    client.force_login(User.objects.create_user(username='boris@example.test'))

    response = client.get(camera_page)

    assert (response.status_code, Viewing.objects.count()) == (
        HTTPStatus.FORBIDDEN,
        0,
    )


@pytest.mark.django_db
def test_sends_a_visitor_to_sign_in(client: Client, camera_page: str) -> None:
    response = client.get(camera_page)

    assert (response.status_code, response.headers.get('Location')) == (
        HTTPStatus.FOUND,
        f'/en/sign-in/?next={camera_page}',
    )


@pytest.mark.django_db
def test_camera_is_never_cached(watcher: Client, camera_page: str) -> None:
    response = watcher.get(camera_page)

    assert 'no-store' in response.headers.get('Cache-Control', '')

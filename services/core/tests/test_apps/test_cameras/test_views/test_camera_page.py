"""Tests of the page of one camera, which records every viewing."""

from http import HTTPStatus

import pytest
from django.test import Client

from server.apps.accounts.models import User
from server.apps.cameras.models import Camera, Viewing


def _page(camera: Camera) -> str:
    """Address of the page of the camera in English."""
    return f'/en/cameras/{camera.pk}/'


@pytest.mark.django_db
def test_the_list_leads_to_the_camera(watcher: Client, camera: Camera) -> None:
    assert f'href="{_page(camera)}"' in watcher.get('/en/cameras/').content.decode()


@pytest.mark.django_db
def test_relative_sees_the_camera(watcher: Client, camera: Camera) -> None:
    assert 'Garden' in watcher.get(_page(camera)).content.decode()


@pytest.mark.django_db
def test_records_who_opened_the_camera(
    watcher: Client,
    camera: Camera,
    relative: User,
) -> None:
    watcher.get(_page(camera))

    assert list(Viewing.objects.values_list('viewer', 'camera')) == [
        (relative.pk, camera.pk),
    ]


@pytest.mark.django_db
def test_a_camera_that_is_off_is_not_found(watcher: Client, camera: Camera) -> None:
    Camera.objects.filter(pk=camera.pk).update(active=False)

    response = watcher.get(_page(camera))

    assert (response.status_code, Viewing.objects.count()) == (
        HTTPStatus.NOT_FOUND,
        0,
    )


@pytest.mark.django_db
@pytest.mark.usefixtures('kinship')
def test_refuses_a_stranger(client: Client, camera: Camera) -> None:
    client.force_login(User.objects.create_user(username='boris@example.test'))

    response = client.get(_page(camera))

    assert (response.status_code, Viewing.objects.count()) == (
        HTTPStatus.FORBIDDEN,
        0,
    )


@pytest.mark.django_db
def test_sends_a_visitor_to_sign_in(client: Client, camera: Camera) -> None:
    response = client.get(_page(camera))

    assert (response.status_code, response.headers.get('Location')) == (
        HTTPStatus.FOUND,
        f'/en/sign-in/?next={_page(camera)}',
    )


@pytest.mark.django_db
def test_camera_is_never_cached(watcher: Client, camera: Camera) -> None:
    response = watcher.get(_page(camera))

    assert 'no-store' in response.headers.get('Cache-Control', '')

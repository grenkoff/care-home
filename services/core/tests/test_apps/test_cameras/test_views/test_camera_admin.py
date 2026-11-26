"""Tests of the admin where staff keep the cameras of the common areas."""

from http import HTTPStatus
from types import MappingProxyType
from typing import Final

import pytest
from django.test import Client

from server.apps.cameras.models import Camera

_ADD: Final = '/admin/cameras/camera/add/'
_GARDEN: Final = MappingProxyType({
    'name_ru': 'Сад',
    'name_en': 'Garden',
    'stream': 'garden',
    'active': 'on',
})


@pytest.mark.django_db
def test_staff_add_a_camera(admin_client: Client) -> None:
    admin_client.post(_ADD, dict(_GARDEN))

    assert list(
        Camera.objects.values_list('name_ru', 'name_en', 'stream', 'active'),
    ) == [('Сад', 'Garden', 'garden', True)]


@pytest.mark.django_db
def test_staff_deactivate_a_camera(admin_client: Client, camera: Camera) -> None:
    admin_client.post(
        f'/admin/cameras/camera/{camera.pk}/change/',
        {**_GARDEN, 'active': ''},
    )

    camera.refresh_from_db()
    assert not camera.active


@pytest.mark.django_db
def test_refuses_a_camera_of_a_taken_stream(
    admin_client: Client,
    camera: Camera,
) -> None:
    response = admin_client.post(_ADD, dict(_GARDEN))

    assert (response.status_code, Camera.objects.count()) == (HTTPStatus.OK, 1)

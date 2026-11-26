"""Tests of the journal of viewings, which staff read but never rewrite."""

from http import HTTPStatus
from typing import Final

import pytest
from django.test import Client

from server.apps.accounts.models import User
from server.apps.cameras.models import Camera, Viewing

_JOURNAL: Final = '/admin/cameras/viewing/'


@pytest.fixture
def viewing(camera: Camera, relative: User) -> Viewing:
    """Viewing of the garden by the relative."""
    return Viewing.objects.create(viewer=relative.pk, camera=camera)


@pytest.mark.django_db
@pytest.mark.usefixtures('viewing')
def test_staff_read_the_journal(admin_client: Client, relative: User) -> None:
    assert str(relative.pk) in admin_client.get(_JOURNAL).content.decode()


@pytest.mark.django_db
def test_staff_cannot_add_a_viewing(admin_client: Client) -> None:
    response = admin_client.get(f'{_JOURNAL}add/')

    assert response.status_code == HTTPStatus.FORBIDDEN


@pytest.mark.django_db
def test_staff_cannot_change_a_viewing(
    admin_client: Client,
    viewing: Viewing,
) -> None:
    response = admin_client.post(f'{_JOURNAL}{viewing.pk}/change/', {})

    assert response.status_code == HTTPStatus.FORBIDDEN


@pytest.mark.django_db
def test_staff_cannot_delete_a_viewing(
    admin_client: Client,
    viewing: Viewing,
) -> None:
    response = admin_client.get(f'{_JOURNAL}{viewing.pk}/delete/')

    assert response.status_code == HTTPStatus.FORBIDDEN


@pytest.mark.django_db
@pytest.mark.parametrize('shown', ['Камеры', 'Журнал просмотров'])
def test_the_admin_of_cameras_speaks_russian(admin_client: Client, shown: str) -> None:
    assert shown in admin_client.get('/admin/cameras/').content.decode()

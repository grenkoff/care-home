"""Fixtures of the tests of cameras."""

import pytest
from django.test import Client

from server.apps.accounts.models import User
from server.apps.cameras.models import Camera
from server.apps.residents.models import Kinship


@pytest.fixture
def camera() -> Camera:
    """Active camera of the garden."""
    return Camera.objects.create(name_ru='Сад', name_en='Garden', stream='garden')


@pytest.fixture
def watcher(client: Client, kinship: Kinship, relative: User) -> Client:
    """Browser of the relative of a resident in the home, signed in."""
    client.force_login(relative)
    return client

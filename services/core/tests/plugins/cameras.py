"""Fixtures of the tests of cameras."""

import pytest

from server.apps.cameras.models import Camera


@pytest.fixture
def camera() -> Camera:
    """Active camera of the garden."""
    return Camera.objects.create(name_ru='Сад', name_en='Garden', stream='garden')

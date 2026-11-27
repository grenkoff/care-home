"""Tests of the home page that introduces the care home."""

import pytest
from django.conf import LazySettings
from django.test import Client

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    ('language', 'phrase'),
    [
        ('ru', 'Небольшой частный дом'),
        ('en', 'A small private care home'),
    ],
)
def test_home_page_introduces_the_home(
    client: Client,
    settings: LazySettings,
    language: str,
    phrase: str,
) -> None:
    page = client.get(f'/{language}/').content.decode()

    assert settings.SITE_NAME in page
    assert phrase in page

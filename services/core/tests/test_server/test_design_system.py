"""Tests of the design system as pages carry and show it."""

import pytest
from django.conf import LazySettings
from django.test import Client
from django.urls import reverse


@pytest.mark.django_db
def test_pages_carry_the_theme_of_the_site(
    client: Client,
    settings: LazySettings,
) -> None:
    response = client.get('/ru/')

    expected = (
        f'<html lang="{settings.LANGUAGE_CODE}" data-theme="{settings.SITE_THEME}">'
    )
    assert expected in response.content.decode()


@pytest.mark.django_db
def test_pages_carry_the_picked_theme(
    client: Client,
    settings: LazySettings,
) -> None:
    settings.SITE_THEME = 'bold'

    response = client.get('/ru/')

    assert 'data-theme="bold"' in response.content.decode()


@pytest.mark.parametrize(
    'fragment',
    [
        'data-theme="classic"',
        'data-theme="warm"',
        'data-theme="bold"',
        'class="ds-button"',
        'class="ds-button-quiet"',
        'ds-card',
        'ds-field',
        'ds-input',
        'ds-alert',
        'ds-heading',
        'ds-price',
    ],
)
def test_design_page_shows_every_component(
    client: Client,
    fragment: str,
) -> None:
    response = client.get(reverse('design'))

    assert fragment in response.content.decode()

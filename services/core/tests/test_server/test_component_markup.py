"""Tests of the markup that web components enhance."""

from html.parser import HTMLParser
from typing import Final, override

import pytest
from django.conf import LazySettings
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

type _Tag = tuple[str, tuple[tuple[str, str | None], ...]]

_HOME: Final = 'care:home'


class _Tags(HTMLParser):
    """Collects the start tags of a page with their attributes."""

    def __init__(self, page: str) -> None:
        """Reads the page."""
        super().__init__()
        self.found: list[_Tag] = []
        self.feed(page)

    @override
    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        """Keeps a start tag."""
        self.found.append((tag, tuple(attrs)))


def _tags(client: Client, url: str) -> list[_Tag]:
    """Returns the start tags of the page at the URL."""
    return _Tags(client.get(url).content.decode()).found


@pytest.mark.parametrize(
    'tag',
    [
        ('site-choice', ()),
        ('select', (('name', 'theme'), ('class', 'ds-input py-1'))),
        ('option', (('value', 'classic'), ('selected', None))),
        ('option', (('value', 'warm'),)),
        ('option', (('value', 'bold'),)),
        ('noscript', ()),
        (
            'script',
            (('type', 'module'), ('src', '/static/components/site-choice.js')),
        ),
    ],
)
def test_header_offers_staff_the_themes(
    admin_client: Client,
    settings: LazySettings,
    tag: _Tag,
) -> None:
    settings.SITE_THEME = 'classic'

    assert tag in _tags(admin_client, reverse(_HOME))


@pytest.mark.parametrize('label', ['<span>Тема</span>', 'Применить'])
def test_header_offers_staff_russian_labels(
    admin_client: Client,
    label: str,
) -> None:
    response = admin_client.get(reverse(_HOME))

    assert label in response.content.decode()


@pytest.mark.django_db
def test_visitors_get_no_theme_switcher(client: Client) -> None:
    response = client.get(reverse(_HOME))

    assert 'name="theme"' not in response.content.decode()


@pytest.mark.django_db
def test_relatives_get_no_theme_switcher(client: Client) -> None:
    client.force_login(get_user_model().objects.create_user(username='relative'))

    response = client.get(reverse(_HOME))

    assert 'name="theme"' not in response.content.decode()


@pytest.mark.django_db
def test_pages_leave_out_the_old_theme_switcher(client: Client) -> None:
    response = client.get(reverse(_HOME))

    assert 'site-theme' not in response.content.decode()

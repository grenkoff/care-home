"""Tests of the links and the language form every page carries."""

import pytest
from django.test import Client


def test_language_form_keeps_the_page(client: Client) -> None:
    response = client.post(
        '/i18n/setlang/',
        {'language': 'en', 'next': '/ru/services/'},
    )

    assert response.headers.get('Location') == '/en/services/'


@pytest.mark.parametrize(
    'fragment',
    [
        'action="/i18n/setlang/"',
        '<input type="hidden" name="next" value="/ru/contacts/">',
        '<option value="en">',
    ],
)
def test_header_offers_the_language_form(client: Client, fragment: str) -> None:
    page = client.get('/ru/contacts/').content.decode()

    assert fragment in page


@pytest.mark.parametrize(
    'link',
    [
        'href="/en/"',
        'href="/en/services/"',
        'href="/en/contacts/"',
        'href="/en/privacy/"',
    ],
)
def test_layout_links_the_pages(client: Client, link: str) -> None:
    page = client.get('/en/contacts/').content.decode()

    assert link in page


@pytest.mark.django_db
@pytest.mark.parametrize(
    'address',
    ['/en/', '/en/services/', '/en/contacts/', '/en/privacy/'],
)
def test_pages_return_to_themselves(client: Client, address: str) -> None:
    page = client.get(address).content.decode()

    assert f'name="next" value="{address}"' in page

"""Tests of the page that tells how to reach the care home."""

import pytest
from django.conf import LazySettings
from django.test import Client


@pytest.mark.parametrize(
    'fragment',
    [
        'href="tel:+70001112233"',
        'href="mailto:desk@garden.test"',
        'href="https://map.test/garden"',
        '12 Sadovaya Street',
        'every day from 10:00 to 20:00',
    ],
)
def test_contacts_tell_how_to_reach_the_home(
    client: Client,
    settings: LazySettings,
    fragment: str,
) -> None:
    settings.SITE_PHONE = '+70001112233'
    settings.SITE_EMAIL = 'desk@garden.test'
    settings.SITE_MAP_URL = 'https://map.test/garden'

    page = client.get('/en/contacts/').content.decode()

    assert fragment in page


def test_contacts_give_the_address_in_russian(client: Client) -> None:
    page = client.get('/ru/contacts/').content.decode()

    assert 'ул. Садовая, 12' in page

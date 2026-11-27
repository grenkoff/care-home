"""Tests of the enquiry form on the contacts page."""

import pytest
from django.test import Client

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    'fragment',
    [
        'action="/en/enquiry/"',
        'Your name',
        'name="name"',
        'name="phone"',
        'Message',
        'name="message"',
        'I agree to the processing of my personal data',
        'name="consent"',
    ],
)
def test_contacts_offer_the_enquiry_form(client: Client, fragment: str) -> None:
    page = client.get('/en/contacts/').content.decode()

    assert fragment in page

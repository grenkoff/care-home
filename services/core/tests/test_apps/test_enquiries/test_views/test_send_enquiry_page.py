"""Tests of the page that takes the enquiry of a visitor."""

from http import HTTPStatus
from types import MappingProxyType
from typing import Final

import pytest
from django.test import Client

from server.apps.enquiries.models import Enquiry

_PAGE: Final = '/en/enquiry/'
_SENT = MappingProxyType({
    'name': 'Anna',
    'phone': ' +7 495 123-45-67 ',
    'message': 'A visit on Sunday',
    'consent': 'on',
})


@pytest.mark.django_db
def test_sent_enquiry_is_kept_for_staff(client: Client) -> None:
    client.post(_PAGE, _SENT)

    kept = Enquiry.objects.get()
    assert (kept.name, kept.phone, kept.message, kept.handled) == (
        'Anna',
        '+7 495 123-45-67',
        'A visit on Sunday',
        False,
    )


@pytest.mark.django_db
def test_sent_enquiry_leads_to_the_received_page(client: Client) -> None:
    response = client.post(_PAGE, _SENT)

    assert response.status_code == HTTPStatus.FOUND
    assert response['Location'] == '/en/enquiry/received/'


def test_enquiry_page_offers_a_blank_form(client: Client) -> None:
    response = client.get(_PAGE)

    assert response.status_code == HTTPStatus.OK
    assert 'name="consent"' in response.content.decode()


def test_received_page_promises_a_call(client: Client) -> None:
    response = client.get('/en/enquiry/received/')

    assert response.status_code == HTTPStatus.OK
    assert 'We will call you back' in response.content.decode()


@pytest.mark.django_db
@pytest.mark.parametrize('missing', ['name', 'phone', 'consent'])
def test_incomplete_enquiry_is_refused(client: Client, missing: str) -> None:
    sent = {field: typed for field, typed in _SENT.items() if field != missing}

    response = client.post(_PAGE, sent)

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert 'This field is required.' in response.content.decode()
    assert not Enquiry.objects.exists()


@pytest.mark.django_db
def test_enquiry_with_a_wrong_phone_is_refused(client: Client) -> None:
    response = client.post(_PAGE, {**_SENT, 'phone': 'call me'})

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert 'Enter a phone number' in response.content.decode()
    assert not Enquiry.objects.exists()


@pytest.mark.django_db
def test_refused_enquiry_keeps_what_was_typed(client: Client) -> None:
    response = client.post(_PAGE, {**_SENT, 'consent': ''})

    assert 'A visit on Sunday</textarea>' in response.content.decode()

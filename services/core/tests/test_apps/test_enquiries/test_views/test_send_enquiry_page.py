"""Tests of the page that takes the enquiry of a visitor."""

from http import HTTPStatus
from types import MappingProxyType

import pytest
from django.test import Client

from server.apps.enquiries.models import Enquiry

_SENT = MappingProxyType({
    'name': 'Anna',
    'phone': ' +7 495 123-45-67 ',
    'message': 'A visit on Sunday',
    'consent': 'on',
})


@pytest.mark.django_db
def test_sent_enquiry_is_kept_for_staff(client: Client) -> None:
    client.post('/en/enquiry/', _SENT)

    assert list(
        Enquiry.objects.values_list('name', 'phone', 'message', 'handled'),
    ) == [('Anna', '+7 495 123-45-67', 'A visit on Sunday', False)]


@pytest.mark.django_db
def test_sent_enquiry_leads_to_the_received_page(client: Client) -> None:
    response = client.post('/en/enquiry/', _SENT)

    assert response.status_code == HTTPStatus.FOUND
    assert response['Location'] == '/en/enquiry/received/'


def test_received_page_promises_a_call(client: Client) -> None:
    response = client.get('/en/enquiry/received/')

    assert response.status_code == HTTPStatus.OK
    assert 'We will call you back' in response.content.decode()

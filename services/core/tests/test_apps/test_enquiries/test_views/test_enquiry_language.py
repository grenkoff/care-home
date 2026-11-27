"""Tests of the enquiry pages in Russian."""

import pytest
from django.test import Client

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    'fragment',
    ['Ваше имя', 'Даю согласие на обработку моих персональных данных'],
)
def test_form_speaks_russian(client: Client, fragment: str) -> None:
    page = client.get('/ru/contacts/').content.decode()

    assert fragment in page


def test_received_page_speaks_russian(client: Client) -> None:
    page = client.get('/ru/enquiry/received/').content.decode()

    assert 'Мы перезвоним' in page


@pytest.mark.django_db
def test_phone_error_speaks_russian(client: Client) -> None:
    page = client.post(
        '/ru/enquiry/',
        {'name': 'Анна', 'phone': 'call me', 'consent': 'on'},
    ).content.decode()

    assert 'Укажите номер телефона' in page

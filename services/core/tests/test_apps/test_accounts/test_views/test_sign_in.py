"""Tests of signing in and out."""

from http import HTTPStatus
from typing import Final

import pytest
from django.test import Client

from server.apps.accounts.models import User

pytestmark = pytest.mark.django_db


_EMAIL: Final = 'anna@example.test'
_CHOSEN: Final = 'a long secret'
_PAGE: Final = '/en/sign-in/'


@pytest.fixture
def relative() -> User:
    """Relative with an account."""
    return User.objects.create_user(username=_EMAIL, email=_EMAIL, password=_CHOSEN)


@pytest.mark.parametrize(
    'fragment',
    [
        'E-mail or user name',
        'type="text"',
        'name="username"',
        'Password',
        'name="password"',
    ],
)
def test_sign_in_asks_for_a_name_and_password(
    client: Client,
    fragment: str,
) -> None:
    assert fragment in client.get(_PAGE).content.decode()


@pytest.mark.django_db
@pytest.mark.usefixtures('relative')
@pytest.mark.parametrize('email', [_EMAIL, 'Anna@Example.TEST'])
def test_password_leads_to_the_second_factor(client: Client, email: str) -> None:
    response = client.post(
        _PAGE,
        {'username': email, 'password': _CHOSEN},
        follow=True,
    )

    assert response.redirect_chain == [
        ('/en/second-factor/', HTTPStatus.FOUND),
        ('/en/second-factor/connect/', HTTPStatus.FOUND),
    ]
    assert 'Sign out' not in response.content.decode()


@pytest.mark.django_db
@pytest.mark.usefixtures('relative')
@pytest.mark.parametrize(
    ('email', 'password'),
    [('boris@example.test', _CHOSEN), (_EMAIL, 'a wrong guess')],
)
def test_wrong_sign_in_names_no_field(
    client: Client,
    email: str,
    password: str,
) -> None:
    page = client.post(
        _PAGE,
        {'username': email, 'password': password},
    ).content.decode()

    assert 'Please enter a correct e-mail or user name and password.' in page
    assert 'Sign out' not in page


@pytest.mark.django_db
def test_relative_signs_out(client: Client, relative: User) -> None:
    client.force_login(relative)

    response = client.post('/en/sign-out/', follow=True)

    assert 'href="/en/sign-in/"' in response.content.decode()


@pytest.mark.django_db
def test_guest_is_offered_to_sign_in(client: Client) -> None:
    assert 'href="/en/sign-in/"' in client.get('/en/').content.decode()

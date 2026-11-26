"""Tests of the page where a relative sees the residents they follow."""

from http import HTTPStatus

import pytest
from django.test import Client

from server.apps.accounts.models import User


@pytest.mark.django_db
@pytest.mark.parametrize('shown', ['Maria Ivanova', '>child<'])
@pytest.mark.usefixtures('kinship')
def test_relative_sees_their_residents(
    client: Client,
    relative: User,
    shown: str,
) -> None:
    client.force_login(relative)

    assert shown in client.get('/en/family/').content.decode()


@pytest.mark.django_db
@pytest.mark.usefixtures('kinship')
def test_hides_residents_of_others(client: Client) -> None:
    client.force_login(User.objects.create_user(username='boris@example.test'))

    assert 'Maria Ivanova' not in client.get('/en/family/').content.decode()


@pytest.mark.django_db
def test_sends_a_visitor_to_sign_in(client: Client) -> None:
    response = client.get('/en/family/')

    assert (response.status_code, response.headers.get('Location')) == (
        HTTPStatus.FOUND,
        '/en/sign-in/?next=/en/family/',
    )


@pytest.mark.django_db
@pytest.mark.parametrize('shown', ['Мои близкие', 'сын или дочь'])
@pytest.mark.usefixtures('kinship')
def test_family_speaks_russian(client: Client, relative: User, shown: str) -> None:
    client.force_login(relative)

    assert shown in client.get('/ru/family/').content.decode()


@pytest.mark.django_db
def test_family_is_never_cached(client: Client, relative: User) -> None:
    client.force_login(relative)

    response = client.get('/en/family/')

    assert 'no-store' in response.headers.get('Cache-Control', '')

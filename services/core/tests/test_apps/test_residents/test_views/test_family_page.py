"""Tests of the page where a relative sees the residents they follow."""

from http import HTTPStatus

import pytest
from django.test import Client

from server.apps.accounts.models import User
from server.apps.residents.models import Kinship, Resident


@pytest.fixture
def follows(resident: Resident, relative: User) -> Kinship:
    """Link of the relative to the resident as a child."""
    return Kinship.objects.create(
        resident=resident,
        kind='child',
        relative=relative.pk,
        granted_by=relative.pk,
    )


@pytest.mark.django_db
@pytest.mark.parametrize('shown', ['Maria Ivanova', 'child'])
@pytest.mark.usefixtures('follows')
def test_relative_sees_their_residents(
    client: Client,
    relative: User,
    shown: str,
) -> None:
    client.force_login(relative)

    assert shown in client.get('/en/family/').content.decode()


@pytest.mark.django_db
@pytest.mark.usefixtures('follows')
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
@pytest.mark.usefixtures('follows')
def test_family_speaks_russian(client: Client, relative: User, shown: str) -> None:
    client.force_login(relative)

    assert shown in client.get('/ru/family/').content.decode()

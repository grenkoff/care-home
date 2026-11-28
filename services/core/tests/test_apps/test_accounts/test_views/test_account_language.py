"""Tests of the pages of accounts in Russian."""

import pytest
from django.test import Client

from server.apps.accounts.models import User


@pytest.mark.django_db
@pytest.mark.usefixtures('invitation')
@pytest.mark.parametrize(
    ('address', 'phrase'),
    [
        ('/ru/sign-in/', 'Пароль'),
        ('/ru/invitation/code-of-anna/', 'никогда не записывайте видео'),
        ('/ru/invitation/guess/', 'Ссылка больше не действует'),
    ],
)
def test_pages_speak_russian(client: Client, address: str, phrase: str) -> None:
    assert phrase in client.get(address).content.decode()


@pytest.mark.django_db
def test_wrong_sign_in_speaks_russian(client: Client) -> None:
    page = client.post(
        '/ru/sign-in/',
        {'username': 'boris@example.test', 'password': 'a wrong guess'},
    ).content.decode()

    assert 'Введите верные e-mail или логин и пароль.' in page


@pytest.mark.django_db
def test_invitation_link_speaks_russian(admin_client: Client) -> None:
    page = admin_client.post(
        '/admin/accounts/invitation/add/',
        {'email': 'anna@example.test'},
        follow=True,
    ).content.decode()

    assert 'Отправьте эту ссылку родственнику' in page


@pytest.mark.django_db
@pytest.mark.usefixtures('invitation')
def test_taken_email_speaks_russian(client: Client) -> None:
    chosen = 'a long secret of anna'
    User.objects.create_user(username='anna@example.test', password=chosen)

    page = client.post(
        '/ru/invitation/code-of-anna/',
        {'new_password1': chosen, 'new_password2': chosen, 'consent': 'on'},
    ).content.decode()

    assert 'уже есть учётная запись' in page

"""Tests of the markup that web components enhance."""

from django.test import Client


def test_pages_leave_out_the_theme_switcher(client: Client) -> None:
    response = client.get('/ru/')

    assert 'site-theme' not in response.content.decode()

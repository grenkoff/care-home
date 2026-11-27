"""Tests of the language dropdown that switches as soon as it is chosen."""

from typing import Final

import pytest
from django.test import Client

_HOME: Final = '/ru/'


@pytest.mark.django_db
def test_language_dropdown_needs_no_button(client: Client) -> None:
    page = client.get(_HOME).content.decode()

    choice = page.partition('<site-choice>')[2].partition('</site-choice>')[0]
    noscript = page.partition('<noscript>')[2].partition('</noscript>')[0]
    assert ('name="language"' in choice, 'Сменить' in noscript) == (True, True)


@pytest.mark.django_db
def test_visitors_get_the_choice_script(client: Client) -> None:
    page = client.get(_HOME).content.decode()

    assert 'src="/static/components/site-choice.js"' in page

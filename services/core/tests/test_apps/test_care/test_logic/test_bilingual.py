"""Tests of texts written in Russian and in English."""

import pytest

from server.apps.care.logic.services import Bilingual, UnknownLanguageError


def test_text_refuses_a_language_the_site_lacks() -> None:
    with pytest.raises(UnknownLanguageError, match='de'):
        Bilingual(russian='Сад', english='Garden').said_in('de')

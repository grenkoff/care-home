"""Texts that the site keeps in each language it speaks."""

from typing import final

import attrs


@final
class UnknownLanguageError(LookupError):
    """Raised when a text is asked for in a language the site does not speak."""

    __slots__ = ()


@final
@attrs.define(slots=True, frozen=True, kw_only=True)
class Bilingual:
    """Text written in Russian and in English."""

    _russian: str
    _english: str

    def said_in(self, language: str) -> str:
        """Returns the text in the language or raises UnknownLanguageError."""
        match language:
            case 'ru':
                return self._russian
            case 'en':
                return self._english
            case _:
                raise UnknownLanguageError(language)

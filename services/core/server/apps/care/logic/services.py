"""Care services of the home, as staff keep them and pages show them."""

from typing import Protocol, final

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


@final
@attrs.define(slots=True, frozen=True)
class Offer:
    """Care service as staff keep it: texts in both languages and its price."""

    name: Bilingual
    description: Bilingual
    price_cents: int


@final
@attrs.define(slots=True, frozen=True)
class CareService:
    """Care service as a page in one language shows it, priced per month."""

    name: str
    description: str
    price_cents: int


class Offers(Protocol):
    """Care services that staff keep."""

    def listed(self) -> list[Offer]:
        """Returns every care service in the order staff set."""

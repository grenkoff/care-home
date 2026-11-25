"""Key of a new authenticator app as the app reads it."""

from typing import Final, final
from urllib.parse import quote, urlencode

import attrs
import segno

_SCALE: Final = 5


@final
@attrs.define(slots=True, frozen=True)
class Enrolment:
    """Key of a new authenticator app as a link and as its QR code."""

    _key: str
    _email: str
    _issuer: str

    def link(self) -> str:
        """Returns the otpauth link that authenticator apps open."""
        label = quote(f'{self._issuer}:{self._email}')
        query = urlencode(
            {'secret': self._key, 'issuer': self._issuer},
            quote_via=quote,
        )
        return f'otpauth://totp/{label}?{query}'

    def picture(self) -> str:
        """Returns the QR code of the link as an SVG data URI."""
        return segno.make(self.link(), error='m').svg_data_uri(scale=_SCALE)

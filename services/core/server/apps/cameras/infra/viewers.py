"""Viewers of the cameras found through the facade of residents."""

import uuid
from typing import final

import attrs

from server.apps.residents.public.kin import Kin


@final
@attrs.define(slots=True, frozen=True)
class KinViewers:
    """Adapter: admits relatives of residents in the home through residents."""

    _kin: Kin

    def admitted(self, viewer: uuid.UUID) -> bool:
        """Tells whether the account has a working link to a resident in the home."""
        return self._kin.related(viewer)

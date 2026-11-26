"""Relatives found in the tables of residents."""

import uuid
from typing import final

import attrs

from server.apps.residents import models


@final
@attrs.define(slots=True, frozen=True)
class StoredKin:
    """Facade: relatives with working links kept in the table of kinships."""

    def related(self, relative: uuid.UUID) -> bool:
        """Tells whether the account has a working link to a resident in the home."""
        return models.Kinship.objects.filter(
            relative=relative,
            revoked_at__isnull=True,
            resident__moved_out_on__isnull=True,
        ).exists()

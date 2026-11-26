"""Families kept in the tables of residents."""

import uuid
from typing import final

import attrs

from server.apps.residents import models
from server.apps.residents.logic.family import Member


@final
@attrs.define(slots=True, frozen=True)
class StoredFamilies:
    """Links of residents to relatives kept in the table of kinships."""

    def members(self, relative: uuid.UUID) -> tuple[Member, ...]:
        """Returns the residents in the home whom the relative follows."""
        rows = (
            models.Kinship.objects
            .filter(
                relative=relative,
                revoked_at__isnull=True,
                resident__moved_out_on__isnull=True,
            )
            .order_by('resident__full_name', 'kind')
            .values_list('resident__full_name', 'kind')
        )
        return tuple(Member(full_name=name, kind=kind) for name, kind in rows)

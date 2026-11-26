"""Relatives found in the copy of accounts that residents keep."""

import uuid
from typing import final

import attrs

from server.apps.residents import models
from server.apps.residents.logic.errors import UnknownRelativeError


@final
@attrs.define(slots=True, frozen=True)
class CopiedRelatives:
    """Relatives found in the copy of accounts that residents keep."""

    def identified(self, email: str) -> uuid.UUID:
        """Returns the account of the e-mail or raises UnknownRelativeError."""
        try:
            return models.Relative.objects.values_list('account', flat=True).get(
                email__iexact=email,
            )
        except models.Relative.DoesNotExist as error:
            raise UnknownRelativeError(email) from error

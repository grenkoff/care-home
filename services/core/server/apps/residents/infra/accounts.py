"""Accounts that residents copy from the facts of accounts."""

from typing import final

import attrs
import msgspec

from server.apps.accounts.public.events import AccountOpened
from server.apps.residents import models
from server.common.outbox.relay import Envelope


@final
@attrs.define(slots=True, frozen=True)
class CopiedAccounts:
    """Observer: copies each opened account, once however often it comes."""

    def receive(self, envelope: Envelope) -> None:
        """Keeps the account once, whichever of its facts comes first."""
        opened = msgspec.convert(envelope.payload, AccountOpened)
        models.Relative.objects.get_or_create(
            account=opened.account,
            defaults={'email': opened.email},
        )

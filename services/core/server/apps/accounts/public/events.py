"""Facts that accounts publish for other modules."""

from typing import Final, final
from uuid import UUID

import msgspec

ACCOUNT_OPENED: Final = 'accounts.v1.account_opened'


@final
class AccountOpened(msgspec.Struct, frozen=True):
    """Fact that an account was opened for an e-mail."""

    id: UUID
    account: UUID
    email: str

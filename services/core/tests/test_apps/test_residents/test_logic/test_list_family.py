"""Tests of listing the residents whom a relative follows."""

import uuid
from typing import Final, final

import attrs

from server.apps.residents.logic.family import Member
from server.apps.residents.logic.usecases.list_family import ListFamily

_ANNA: Final = uuid.UUID('01900000-0000-7000-8000-000000000001')
_MARIA: Final = Member(full_name='Maria Ivanova', kind='child')


@final
@attrs.define(slots=True, frozen=True)
class _Families:
    """Families in which only Anna follows Maria."""

    def members(self, relative: uuid.UUID) -> tuple[Member, ...]:
        """Returns Maria for Anna and nobody for anyone else."""
        return (_MARIA,) if relative == _ANNA else ()


def test_lists_the_residents_of_a_relative() -> None:
    assert ListFamily(_Families())(_ANNA) == (_MARIA,)

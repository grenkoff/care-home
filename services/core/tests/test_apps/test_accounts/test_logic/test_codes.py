"""Tests of the codes of authenticator apps."""

from datetime import UTC, datetime
from typing import Final

import pytest

from server.apps.accounts.logic.codes import Key, Totp
from server.apps.accounts.logic.errors import WrongCodeError

_KEY: Final = Key('GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ')
_MOMENT: Final = datetime.fromtimestamp(1111111111, tz=UTC)
_STEP: Final = 37037037


@pytest.mark.parametrize(
    ('seconds', 'code'),
    [
        (59, '287082'),
        (1111111109, '081804'),
        (1111111111, '050471'),
        (1234567890, '005924'),
        (2000000000, '279037'),
        (20000000000, '353130'),
    ],
)
def test_key_gives_the_codes_of_the_rfc(seconds: int, code: str) -> None:
    assert _KEY.code(seconds // 30) == code


@pytest.mark.parametrize('step', [_STEP - 1, _STEP, _STEP + 1])
def test_code_of_a_near_step_is_accepted(step: int) -> None:
    assert Totp(_KEY, 0).accepted(_KEY.code(step), _MOMENT) == step


@pytest.mark.parametrize('step', [_STEP - 2, _STEP + 2])
def test_code_of_a_far_step_is_refused(step: int) -> None:
    with pytest.raises(WrongCodeError):
        Totp(_KEY, 0).accepted(_KEY.code(step), _MOMENT)


def test_wrong_code_is_refused() -> None:
    with pytest.raises(WrongCodeError):
        Totp(_KEY, 0).accepted('000000', _MOMENT)


@pytest.mark.parametrize('used', [_STEP, _STEP + 1])
def test_code_already_used_is_refused(used: int) -> None:
    with pytest.raises(WrongCodeError):
        Totp(_KEY, used).accepted(_KEY.code(_STEP), _MOMENT)


def test_code_after_the_used_one_is_accepted() -> None:
    totp = Totp(_KEY, _STEP - 1)

    assert totp.accepted(_KEY.code(_STEP), _MOMENT) == _STEP

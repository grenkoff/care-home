"""Forms of the residents and their relatives."""

import uuid
from typing import Any, final, override

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from server.apps.residents.logic.errors import UnknownRelativeError
from server.apps.residents.logic.usecases import find_relative


@final
class RelativeField(forms.EmailField):
    """E-mail that staff type, turned into the account of the relative."""

    def __init__(self, find: find_relative.FindRelative, **kwargs: Any) -> None:
        """Keeps the use case that finds accounts by e-mail."""
        super().__init__(**kwargs)
        self._find = find

    @override
    def clean(self, typed: Any) -> uuid.UUID:
        """Returns the account of the e-mail or refuses an unknown one."""
        try:
            return self._find(super().clean(typed))
        except UnknownRelativeError as error:
            raise ValidationError(
                _('No account has this e-mail. Invite the relative first.'),
                code='unknown',
            ) from error

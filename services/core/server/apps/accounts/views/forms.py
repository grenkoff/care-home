"""Forms of the pages of accounts."""

from typing import final

from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext

from server.apps.accounts.logic.constants import CODE_LOCK_MINUTES


@final
class RulesForm(forms.Form):
    """Consent of a relative to the rules of watching the cameras."""

    consent = forms.BooleanField(
        label=_('I accept the rules of watching'),
    )


@final
class CodeForm(forms.Form):
    """Six-digit code that an authenticator app shows."""

    code = forms.RegexField(
        regex=r'\A[0-9]{6}\Z',
        label=_('Code'),
        error_messages={'invalid': _('Enter the six digits that the app shows.')},
    )

    def refuse(self) -> None:
        """Marks the code as one that the authenticator app did not give."""
        self.add_error('code', _('This code is wrong or no longer valid.'))

    def lock(self) -> None:
        """Marks the codes as locked for a while after too many wrong ones."""
        self.add_error(
            'code',
            ngettext(
                'Too many wrong codes. Try again in %(minutes)d minute.',
                'Too many wrong codes. Try again in %(minutes)d minutes.',
                CODE_LOCK_MINUTES,
            )
            % {'minutes': CODE_LOCK_MINUTES},
        )

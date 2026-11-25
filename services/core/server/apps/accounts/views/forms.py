"""Forms of the pages of accounts."""

from typing import final

from django import forms
from django.utils.translation import gettext_lazy as _


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

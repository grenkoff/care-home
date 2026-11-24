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

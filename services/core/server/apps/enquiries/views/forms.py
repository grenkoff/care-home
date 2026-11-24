"""Forms of the pages of enquiries."""

from typing import Final, final

from django import forms
from django.utils.translation import gettext_lazy as _

from server.apps.enquiries.logic.constants import (
    MESSAGE_MAX_LENGTH,
    NAME_MAX_LENGTH,
    PHONE_MAX_LENGTH,
)

_INPUT: Final = 'ds-input'


@final
class EnquiryForm(forms.Form):
    """Enquiry that a visitor fills in to be called back."""

    name = forms.CharField(
        label=_('Your name'),
        max_length=NAME_MAX_LENGTH,
        widget=forms.TextInput(attrs={'class': _INPUT, 'autocomplete': 'name'}),
    )
    phone = forms.CharField(
        label=_('Phone'),
        max_length=PHONE_MAX_LENGTH,
        widget=forms.TextInput(
            attrs={'class': _INPUT, 'autocomplete': 'tel', 'inputmode': 'tel'},
        ),
    )
    message = forms.CharField(
        label=_('Message'),
        required=False,
        max_length=MESSAGE_MAX_LENGTH,
        widget=forms.Textarea(attrs={'class': _INPUT, 'rows': 4}),
    )
    consent = forms.BooleanField(
        label=_('I agree to the processing of my personal data'),
    )

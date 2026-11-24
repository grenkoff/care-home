"""Pages of enquiries rendered on the server."""

from http import HTTPStatus
from typing import final

from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.utils.translation import gettext_lazy as _
from django.views import View

from server.apps.enquiries.logic.phone import InvalidPhoneError
from server.apps.enquiries.logic.usecases import send_enquiry
from server.apps.enquiries.views.forms import EnquiryForm
from server.common.di import HasContainer


@final
class Send(HasContainer, View):
    """Page that takes the enquiry of a visitor."""

    def post(self, request: HttpRequest) -> HttpResponse:
        """Keeps the enquiry and leads on, or shows the form with its errors."""
        form = EnquiryForm(request.POST)
        if form.is_valid():
            try:
                self.resolve(send_enquiry.SendEnquiry)(
                    name=form.cleaned_data['name'],
                    phone=form.cleaned_data['phone'],
                    message=form.cleaned_data['message'],
                )
            except InvalidPhoneError:
                form.add_error(
                    'phone',
                    _('Enter a phone number, for example +7 495 123-45-67.'),
                )
            else:
                return redirect('enquiries:received')
        return render(
            request,
            'enquiries/send.html',
            {'form': form},
            status=HTTPStatus.BAD_REQUEST,
        )

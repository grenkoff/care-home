"""Pages of enquiries rendered on the server."""

from typing import final

from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect
from django.views import View

from server.apps.enquiries.logic.usecases import send_enquiry
from server.apps.enquiries.views.forms import EnquiryForm
from server.common.di import HasContainer


@final
class Send(HasContainer, View):
    """Page that takes the enquiry of a visitor."""

    def post(self, request: HttpRequest) -> HttpResponse:
        """Keeps the enquiry and leads to the received page."""
        form = EnquiryForm(request.POST)
        if not form.is_valid():
            return HttpResponseBadRequest()
        self.resolve(send_enquiry.SendEnquiry)(
            name=form.cleaned_data['name'],
            phone=form.cleaned_data['phone'],
            message=form.cleaned_data['message'],
        )
        return redirect('enquiries:received')

"""Routes of the pages of enquiries."""

from django.urls import path
from django.views.generic import TemplateView

from server.apps.enquiries.views import pages

urlpatterns = [
    path('enquiry/', pages.Send.as_view(), name='send'),
    path(
        'enquiry/received/',
        TemplateView.as_view(template_name='enquiries/received.html'),
        name='received',
    ),
]

"""Routes of the pages of enquiries."""

from django.urls import path

from server.apps.enquiries.views import pages

urlpatterns = [
    path('enquiry/', pages.Send.as_view(), name='send'),
]

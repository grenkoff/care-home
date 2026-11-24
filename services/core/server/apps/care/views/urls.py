"""Routes of the pages of care."""

from django.urls import path
from django.views.generic import TemplateView

from server.apps.care.views import pages

urlpatterns = [
    path('', TemplateView.as_view(template_name='care/home.html'), name='home'),
    path('services/', pages.Services.as_view(), name='services'),
    path('contacts/', pages.Contacts.as_view(), name='contacts'),
    path(
        'privacy/',
        TemplateView.as_view(template_name='care/privacy.html'),
        name='privacy',
    ),
]

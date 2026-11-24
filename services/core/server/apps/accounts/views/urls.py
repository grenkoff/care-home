"""Routes of the pages of accounts."""

from django.contrib.auth import views
from django.urls import path

from server.apps.accounts.views import pages

urlpatterns = [
    path(
        'sign-in/',
        views.LoginView.as_view(
            template_name='accounts/sign_in.html',
            redirect_authenticated_user=True,
        ),
        name='sign_in',
    ),
    path('sign-out/', views.LogoutView.as_view(), name='sign_out'),
    path('invitation/<str:code>/', pages.Accept.as_view(), name='accept'),
]

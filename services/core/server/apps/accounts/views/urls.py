"""Routes of the pages of accounts."""

from django.contrib.auth import views
from django.urls import path, reverse_lazy

from server.apps.accounts.views import pages, second_factor, sign_in

urlpatterns = [
    path('sign-in/', sign_in.SignIn.as_view(), name='sign_in'),
    path('second-factor/', second_factor.Code.as_view(), name='code'),
    path(
        'second-factor/connect/',
        second_factor.Connect.as_view(),
        name='connect',
    ),
    path('sign-out/', views.LogoutView.as_view(), name='sign_out'),
    path(
        'password/',
        views.PasswordChangeView.as_view(
            template_name='accounts/password.html',
            success_url=reverse_lazy('accounts:password_changed'),
        ),
        name='password',
    ),
    path(
        'password/done/',
        views.PasswordChangeDoneView.as_view(
            template_name='accounts/password_changed.html',
        ),
        name='password_changed',
    ),
    path('invitation/<str:code>/', pages.Accept.as_view(), name='accept'),
]

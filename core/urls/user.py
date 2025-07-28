from django.urls import path

from core.views.request import UserRequestListView
from core.views.user import UserDonationView, UserEditView, UserView

urlpatterns = [
    path("me/", UserView.as_view(), name="user_me"),
    path("<uuid:pk>/", UserView.as_view(), name="user"),
    path("me/edit/", UserEditView.as_view(), name="user_me_edit"),
    path("me/requests/", UserRequestListView.as_view(), name="user_me_requests"),
    path("<uuid:pk>/donate/", UserDonationView.as_view(), name="user_donate"),
]

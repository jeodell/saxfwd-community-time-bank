from django.urls import path

from core.views.user import UserEditView, UserView

urlpatterns = [
    path("me/", UserView.as_view(), name="user_me"),
    path("me/edit/", UserEditView.as_view(), name="user_me_edit"),
    path("<uuid:pk>/", UserView.as_view(), name="user"),
    path("<uuid:pk>/edit/", UserEditView.as_view(), name="user_edit"),
]

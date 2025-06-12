from django.urls import path

from core.views.user import RegisterView, UserEditView, UserListView, UserView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("users/", UserListView.as_view(), name="user_list"),
    path("users/me/", UserView.as_view(), name="user_me"),
    path("users/me/edit/", UserEditView.as_view(), name="user_me_edit"),
    path("users/<uuid:pk>/", UserView.as_view(), name="user"),
    path("users/<uuid:pk>/edit/", UserEditView.as_view(), name="user_edit"),
]

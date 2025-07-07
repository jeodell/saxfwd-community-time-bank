from django.urls import path

from core.views.request import (
    RequestCreateView,
    RequestDeleteView,
    RequestDetailView,
    RequestEditView,
    RequestListView,
    RequestToggleActiveView,
    RequestTransactionView,
)

urlpatterns = [
    path("", RequestListView.as_view(), name="request_list"),
    path(
        "create/",
        RequestCreateView.as_view(),
        name="request_create",
    ),
    path(
        "<uuid:pk>/",
        RequestDetailView.as_view(),
        name="request_detail",
    ),
    path(
        "<uuid:pk>/edit/",
        RequestEditView.as_view(),
        name="request_edit",
    ),
    path(
        "<uuid:pk>/offer/",
        RequestTransactionView.as_view(),
        name="request_offer",
    ),
    path(
        "<uuid:pk>/toggle-active/",
        RequestToggleActiveView.as_view(),
        name="request_toggle_active",
    ),
    path(
        "<uuid:pk>/delete/",
        RequestDeleteView.as_view(),
        name="request_delete",
    ),
]

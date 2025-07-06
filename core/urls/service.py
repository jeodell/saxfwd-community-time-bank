from django.urls import path

from core.views.service import (
    ServiceCreateView,
    ServiceDeleteView,
    ServiceDetailView,
    ServiceEditView,
    ServiceListView,
    ServiceToggleActiveView,
    ServiceTransactionView,
)

urlpatterns = [
    path("", ServiceListView.as_view(), name="service_list"),
    path("create/", ServiceCreateView.as_view(), name="service_create"),
    path(
        "<uuid:pk>/",
        ServiceDetailView.as_view(),
        name="service_detail",
    ),
    path(
        "<uuid:pk>/edit/",
        ServiceEditView.as_view(),
        name="service_edit",
    ),
    path(
        "<uuid:pk>/delete/",
        ServiceDeleteView.as_view(),
        name="service_delete",
    ),
    path(
        "<uuid:pk>/transaction/",
        ServiceTransactionView.as_view(),
        name="service_transaction",
    ),
    path(
        "<uuid:pk>/toggle-active/",
        ServiceToggleActiveView.as_view(),
        name="service_toggle_active",
    ),
]

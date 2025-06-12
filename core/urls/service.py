from django.urls import path

from core.views.service import (
    ServiceCreateView,
    ServiceDeleteView,
    ServiceDetailView,
    ServiceEditView,
    ServiceListView,
    ServiceRequestView,
    ServiceToggleActiveView,
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
        "<uuid:pk>/request/",
        ServiceRequestView.as_view(),
        name="service_request",
    ),
    path(
        "<uuid:pk>/toggle-active/",
        ServiceToggleActiveView.as_view(),
        name="service_toggle_active",
    ),
]

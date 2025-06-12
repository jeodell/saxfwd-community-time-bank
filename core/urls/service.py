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
    path("services/", ServiceListView.as_view(), name="service_list"),
    path("services/create/", ServiceCreateView.as_view(), name="service_create"),
    path(
        "services/<uuid:pk>/",
        ServiceDetailView.as_view(),
        name="service_detail",
    ),
    path(
        "services/<uuid:pk>/edit/",
        ServiceEditView.as_view(),
        name="service_edit",
    ),
    path(
        "services/<uuid:pk>/delete/",
        ServiceDeleteView.as_view(),
        name="service_delete",
    ),
    path(
        "services/<uuid:pk>/request/",
        ServiceRequestView.as_view(),
        name="service_request",
    ),
    path(
        "services/<uuid:pk>/toggle-active/",
        ServiceToggleActiveView.as_view(),
        name="service_toggle_active",
    ),
]

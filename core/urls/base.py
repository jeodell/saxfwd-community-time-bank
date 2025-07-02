from django.urls import path

from core.views.base import (
    AboutView,
    ApplicationReviewDetailView,
    ApplicationReviewListView,
    ApplicationSubmittedView,
    ApplicationView,
    HomeView,
    MarkUserOnboardedView,
    PasswordSetupView,
)

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("about/", AboutView.as_view(), name="about"),
    path("accounts/apply/", ApplicationView.as_view(), name="apply"),
    path(
        "accounts/application-submitted/",
        ApplicationSubmittedView.as_view(),
        name="application_submitted",
    ),
    path(
        "accounts/password-setup/", PasswordSetupView.as_view(), name="password_setup"
    ),
    # Staff application review URLs
    path(
        "admin/applications/",
        ApplicationReviewListView.as_view(),
        name="application_review_list",
    ),
    path(
        "admin/applications/<uuid:application_id>/",
        ApplicationReviewDetailView.as_view(),
        name="application_review_detail",
    ),
    path(
        "admin/users/<uuid:user_id>/mark-onboarded/",
        MarkUserOnboardedView.as_view(),
        name="mark_user_onboarded",
    ),
]

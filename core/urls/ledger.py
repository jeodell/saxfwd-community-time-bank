from django.urls import path

from core.views.ledger import DonateCommunityHoursView, LedgerView

urlpatterns = [
    path("", LedgerView.as_view(), name="ledger"),
    path("donate/", DonateCommunityHoursView.as_view(), name="donate_community_hours"),
]

from django.urls import path

from core.views.ledger import LedgerView

urlpatterns = [
    path("", LedgerView.as_view(), name="ledger"),
]

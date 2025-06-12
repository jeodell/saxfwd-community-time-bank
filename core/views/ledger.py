from django.views.generic import ListView

from ..models import TimeBankLedger


class LedgerView(ListView):
    model = TimeBankLedger
    template_name = "core/ledger.html"
    context_object_name = "transactions"
    paginate_by = 50  # Show 50 transactions per page

    def get_queryset(self):
        # Get all transactions and order by created_at
        transactions = TimeBankLedger.objects.all().order_by("-created_at")

        # Group transactions by service request
        grouped_transactions = {}
        for transaction in transactions:
            # Use service request as the key for grouping
            key = transaction.service_request_id
            if key not in grouped_transactions:
                grouped_transactions[key] = {
                    "created_at": transaction.created_at,
                    "service_request": transaction.service_request,
                    "hours": transaction.hours,
                    "description": transaction.service_request.service.title
                    if transaction.service_request
                    else "Community Hours",
                    "from_user": transaction.service_request.requester
                    if transaction.service_request
                    else None,
                    "to_user": transaction.service_request.service.provider
                    if transaction.service_request
                    else None,
                }

        # Convert the grouped transactions to a list and sort by date
        return sorted(
            grouped_transactions.values(), key=lambda x: x["created_at"], reverse=True
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["total_transactions"] = len(self.get_queryset())
        context["total_hours_exchanged"] = sum(t["hours"] for t in self.get_queryset())
        return context

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import DetailView, ListView, View

from ..forms import (
    ServiceTransactionCancelForm,
    ServiceTransactionCompleteForm,
    ServiceTransactionRejectForm,
)
from ..models import Request, ServiceTransaction


class UserRequestListView(LoginRequiredMixin, ListView):
    model = ServiceTransaction
    template_name = "my_requests/request_list.html"
    context_object_name = "requests"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get status parameters for each column
        by_me_status = self.request.GET.get("by_me_status")
        to_me_status = self.request.GET.get("to_me_status")

        # Base querysets for each column
        my_requests = ServiceTransaction.objects.filter(requester=self.request.user)
        requests_to_me = ServiceTransaction.objects.filter(
            service__provider=self.request.user
        )

        # Apply status filters for my requests
        if by_me_status:
            if by_me_status == "active":
                my_requests = my_requests.filter(status__in=["pending", "accepted"])
            elif by_me_status == "closed":
                my_requests = my_requests.filter(status__in=["rejected", "canceled"])
            else:
                my_requests = my_requests.filter(status=by_me_status)
        else:
            # Default to active requests if no status specified
            my_requests = my_requests.filter(status__in=["pending", "accepted"])

        # Apply status filters for requests to me
        if to_me_status:
            if to_me_status == "active":
                requests_to_me = requests_to_me.filter(
                    status__in=["pending", "accepted"]
                )
            elif to_me_status == "closed":
                requests_to_me = requests_to_me.filter(
                    status__in=["rejected", "canceled"]
                )
            else:
                requests_to_me = requests_to_me.filter(status=to_me_status)
        else:
            # Default to active requests if no status specified
            requests_to_me = requests_to_me.filter(status__in=["pending", "accepted"])

        # Order both querysets
        context["my_requests"] = my_requests.order_by("-created_at")
        context["requests_to_me"] = requests_to_me.order_by("-created_at")

        return context


class RequestDetailView(LoginRequiredMixin, DetailView):
    model = ServiceTransaction
    template_name = "services/service_transaction_detail.html"
    context_object_name = "request"

    def get_object(self):
        obj = super().get_object()
        if (
            self.request.user != obj.requester
            and self.request.user != obj.service.provider
        ):
            messages.error(
                self.request, "You do not have permission to view this request."
            )
            return redirect("home")
        return obj


class RequestAcceptView(LoginRequiredMixin, View):
    def post(self, request, pk):
        service_transaction = get_object_or_404(ServiceTransaction, pk=pk)
        if request.user != service_transaction.service.provider:
            messages.error(request, "Only the service provider can accept requests.")
            return redirect("home")

        try:
            service_transaction.accept_request()
            messages.success(request, "Request accepted successfully!")
        except ValueError as e:
            messages.error(request, str(e))
        return redirect("request_detail", pk=pk)


class RequestRejectView(LoginRequiredMixin, View):
    def post(self, request, pk):
        service_transaction = get_object_or_404(ServiceTransaction, pk=pk)
        if request.user != service_transaction.service.provider:
            messages.error(request, "Only the service provider can reject requests.")
            return redirect("home")

        form = ServiceTransactionRejectForm(request.POST)
        if form.is_valid():
            try:
                rejection_reason = form.cleaned_data["rejection_reason"]
                service_transaction.reject_request(rejection_reason)
                messages.success(request, "Request rejected successfully!")
            except ValueError as e:
                messages.error(request, str(e))
        else:
            messages.error(
                request, "Please provide a reason for rejecting the request."
            )

        return redirect("request_detail", pk=pk)


class RequestCancelView(LoginRequiredMixin, View):
    def post(self, request, pk):
        service_transaction = get_object_or_404(ServiceTransaction, pk=pk)
        if request.user != service_transaction.requester:
            messages.error(request, "Only the requester can cancel requests.")
            return redirect("home")

        form = ServiceTransactionCancelForm(request.POST)
        if form.is_valid():
            try:
                cancellation_reason = form.cleaned_data.get("cancellation_reason", "")
                service_transaction.cancel_request(cancellation_reason)
                messages.success(request, "Request canceled successfully!")
            except ValueError as e:
                messages.error(request, str(e))
        else:
            messages.error(request, "There was an error processing your request.")

        return redirect("request_detail", pk=pk)


class RequestCompleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        service_transaction = get_object_or_404(ServiceTransaction, pk=pk)

        try:
            is_fully_completed = service_transaction.complete_request(request.user)
            if is_fully_completed:
                messages.success(
                    request,
                    "Request completed successfully! Time credits have been transferred.",
                )
            else:
                messages.success(
                    request,
                    "Completion status updated. Waiting for the other party to complete.",
                )
        except ValueError as e:
            messages.error(request, str(e))
            return redirect("home")

        return redirect("request_detail", pk=pk)


class RequestCompleteFormView(LoginRequiredMixin, View):
    template_name = "services/service_transaction_complete_form.html"

    def get(self, request, pk):
        service_transaction = get_object_or_404(ServiceTransaction, pk=pk)

        # Check if user has permission to complete this request
        if (
            request.user != service_transaction.service.provider
            and request.user != service_transaction.requester
        ):
            messages.error(
                request, "You do not have permission to complete this request."
            )
            return redirect("home")

        # Check if request is in a state that can be completed
        if service_transaction.status != "accepted":
            messages.error(request, "This request cannot be completed at this time.")
            return redirect("request_detail", pk=pk)

        # Check if user has already completed their part
        if (
            request.user == service_transaction.service.provider
            and service_transaction.provider_completed
        ):
            messages.error(
                request, "You have already marked this request as completed."
            )
            return redirect("request_detail", pk=pk)
        if (
            request.user == service_transaction.requester
            and service_transaction.requester_completed
        ):
            messages.error(
                request, "You have already confirmed this request as completed."
            )
            return redirect("request_detail", pk=pk)

        form = ServiceTransactionCompleteForm(
            initial={"hours_completed": service_transaction.hours_requested}
        )
        return render(
            request, self.template_name, {"request": service_transaction, "form": form}
        )

    def post(self, request, pk):
        service_transaction = get_object_or_404(ServiceTransaction, pk=pk)

        # Check if user has permission to complete this request
        if (
            request.user != service_transaction.service.provider
            and request.user != service_transaction.requester
        ):
            messages.error(
                request, "You do not have permission to complete this request."
            )
            return redirect("home")

        # Check if request is in a state that can be completed
        if service_transaction.status != "accepted":
            messages.error(request, "This request cannot be completed at this time.")
            return redirect("request_detail", pk=pk)

        # Check if user has already completed their part
        if (
            request.user == service_transaction.service.provider
            and service_transaction.provider_completed
        ):
            messages.error(
                request, "You have already marked this request as completed."
            )
            return redirect("request_detail", pk=pk)
        if (
            request.user == service_transaction.requester
            and service_transaction.requester_completed
        ):
            messages.error(
                request, "You have already confirmed this request as completed."
            )
            return redirect("request_detail", pk=pk)

        form = ServiceTransactionCompleteForm(request.POST)
        if form.is_valid():
            hours_completed = form.cleaned_data["hours_completed"]
            try:
                is_fully_completed = service_transaction.complete_request(
                    request.user, hours_completed=hours_completed
                )
                if is_fully_completed:
                    messages.success(
                        request,
                        "Request completed successfully! Time credits have been transferred.",
                    )
                else:
                    messages.success(
                        request,
                        "Completion status updated. Waiting for the other party to complete.",
                    )
            except ValueError as e:
                messages.error(request, str(e))
                return redirect("request_detail", pk=pk)

            return redirect("request_detail", pk=pk)

        return render(
            request, self.template_name, {"request": service_transaction, "form": form}
        )


class RequestCommunityHoursView(LoginRequiredMixin, View):
    def get(self, request, pk):
        service_transaction = get_object_or_404(ServiceTransaction, pk=pk)
        if not service_transaction.can_request_community_hours():
            messages.error(
                request, "This request cannot be converted to a community request."
            )
            return redirect("request_detail", pk=pk)
        return render(
            request,
            "services/service_transaction_form.html",
            {"request": service_transaction},
        )

    def post(self, request, pk):
        service_transaction = get_object_or_404(ServiceTransaction, pk=pk)
        if request.user != service_transaction.requester:
            messages.error(
                request, "Only the requester can convert to a community request."
            )
            return redirect("request_detail", pk=pk)

        if not service_transaction.can_request_community_hours():
            messages.error(
                request, "This request cannot be converted to a community request."
            )
            return redirect("request_detail", pk=pk)

        reason = request.POST.get("reason", "")
        if not reason:
            messages.error(
                request, "Please provide a reason for requesting community hours."
            )
            return redirect("request_detail", pk=pk)

        service_transaction.request_community_hours(reason)
        messages.success(request, "Community hours request submitted successfully!")
        return redirect("request_detail", pk=pk)


class ApproveCommunityTransactionView(LoginRequiredMixin, UserPassesTestMixin, View):
    def get(self, request, pk):
        service_transaction = get_object_or_404(ServiceTransaction, pk=pk)
        if not service_transaction.can_be_approved():
            messages.error(request, "This request cannot be approved.")
            return redirect("request_detail", pk=pk)
        return render(
            request,
            "requests/community_request_review.html",
            {"request": service_transaction},
        )

    def post(self, request, pk):
        service_transaction = get_object_or_404(ServiceTransaction, pk=pk)
        if not service_transaction.can_be_approved():
            messages.error(request, "This request cannot be approved.")
            return redirect("request_detail", pk=pk)

        notes = request.POST.get("notes", "")
        try:
            service_transaction.approve_community_request(request.user, notes)
            messages.success(request, "Community hours request approved successfully!")
        except ValueError as e:
            messages.error(request, str(e))
        return redirect("request_detail", pk=pk)


class RejectCommunityTransactionView(LoginRequiredMixin, UserPassesTestMixin, View):
    def get(self, request, pk):
        service_transaction = get_object_or_404(ServiceTransaction, pk=pk)
        if not service_transaction.can_be_rejected():
            messages.error(request, "This request cannot be rejected.")
            return redirect("request_detail", pk=pk)
        return render(
            request,
            "requests/community_request_review.html",
            {"request": service_transaction},
        )

    def post(self, request, pk):
        service_transaction = get_object_or_404(ServiceTransaction, pk=pk)
        if not service_transaction.can_be_rejected():
            messages.error(request, "This request cannot be rejected.")
            return redirect("request_detail", pk=pk)

        notes = request.POST.get("notes", "")
        service_transaction.reject_community_request(request.user, notes)
        messages.success(request, "Community hours request rejected.")
        return redirect("request_detail", pk=pk)


class RequestListView(LoginRequiredMixin, ListView):
    model = Request
    template_name = "requests/request_list.html"
    context_object_name = "requests"
    paginate_by = 20

    def get_queryset(self):
        """Get active community requests, excluding the current user's own requests."""
        queryset = Request.get_active_requests(exclude_user=self.request.user)

        # Apply category filter if provided
        category = self.request.GET.get("category")
        if category:
            queryset = queryset.filter(category__name=category)

        # Apply search filter if provided
        search = self.request.GET.get("search")
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from ..models import ServiceCategory

        # Add categories for filtering
        context["categories"] = ServiceCategory.objects.all().order_by("name")

        # Add search and filter parameters
        context["current_category"] = self.request.GET.get("category")
        context["current_search"] = self.request.GET.get("search")

        return context

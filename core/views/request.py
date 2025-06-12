from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import DetailView, ListView, View

from ..forms import ServiceRequestCompleteForm, ServiceRequestRejectForm
from ..models import ServiceRequest


class RequestListView(LoginRequiredMixin, ListView):
    model = ServiceRequest
    template_name = "requests/request_list.html"
    context_object_name = "requests"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get status parameters for each column
        by_me_status = self.request.GET.get("by_me_status")
        to_me_status = self.request.GET.get("to_me_status")

        # Base querysets for each column
        my_requests = ServiceRequest.objects.filter(requester=self.request.user)
        requests_to_me = ServiceRequest.objects.filter(
            service__provider=self.request.user
        )

        # Apply status filters for my requests
        if by_me_status:
            if by_me_status == "active":
                my_requests = my_requests.filter(status__in=["pending", "accepted"])
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
    model = ServiceRequest
    template_name = "requests/request_detail.html"
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
        service_request = get_object_or_404(ServiceRequest, pk=pk)
        if request.user != service_request.service.provider:
            messages.error(request, "Only the service provider can accept requests.")
            return redirect("home")

        try:
            service_request.accept_request()
            messages.success(request, "Request accepted successfully!")
        except ValueError as e:
            messages.error(request, str(e))
        return redirect("request_detail", pk=pk)


class RequestRejectView(LoginRequiredMixin, View):
    def post(self, request, pk):
        service_request = get_object_or_404(ServiceRequest, pk=pk)
        if request.user != service_request.service.provider:
            messages.error(request, "Only the service provider can reject requests.")
            return redirect("home")

        form = ServiceRequestRejectForm(request.POST)
        if form.is_valid():
            try:
                rejection_reason = form.cleaned_data["rejection_reason"]
                service_request.reject_request(rejection_reason)
                messages.success(request, "Request rejected successfully!")
            except ValueError as e:
                messages.error(request, str(e))
        else:
            messages.error(
                request, "Please provide a reason for rejecting the request."
            )
            return redirect("request_reject_form", pk=pk)

        return redirect("request_detail", pk=pk)


class RequestRejectFormView(LoginRequiredMixin, View):
    template_name = "requests/request_reject_form.html"

    def get(self, request, pk):
        service_request = get_object_or_404(ServiceRequest, pk=pk)
        if request.user != service_request.service.provider:
            messages.error(request, "Only the service provider can reject requests.")
            return redirect("home")

        if service_request.status != "pending":
            messages.error(request, "This request cannot be rejected.")
            return redirect("request_detail", pk=pk)

        form = ServiceRequestRejectForm()
        return render(
            request, self.template_name, {"request": service_request, "form": form}
        )

    def post(self, request, pk):
        service_request = get_object_or_404(ServiceRequest, pk=pk)
        if request.user != service_request.service.provider:
            messages.error(request, "Only the service provider can reject requests.")
            return redirect("home")

        if service_request.status != "pending":
            messages.error(request, "This request cannot be rejected.")
            return redirect("request_detail", pk=pk)

        form = ServiceRequestRejectForm(request.POST)
        if form.is_valid():
            rejection_reason = form.cleaned_data["rejection_reason"]
            try:
                service_request.reject_request(rejection_reason)
                messages.success(request, "Request rejected successfully!")
                return redirect("request_detail", pk=pk)
            except ValueError as e:
                messages.error(request, str(e))
        else:
            messages.error(
                request, "Please provide a reason for rejecting the request."
            )

        return render(
            request, self.template_name, {"request": service_request, "form": form}
        )


class RequestCancelView(LoginRequiredMixin, View):
    def post(self, request, pk):
        service_request = get_object_or_404(ServiceRequest, pk=pk)
        if request.user != service_request.requester:
            messages.error(request, "Only the requester can cancel requests.")
            return redirect("home")

        try:
            service_request.cancel_request()
            messages.success(request, "Request cancelled successfully!")
            return redirect("request_detail", pk=pk)
        except ValueError as e:
            messages.error(request, str(e))
        return redirect("request_detail", pk=pk)


class RequestCompleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        service_request = get_object_or_404(ServiceRequest, pk=pk)

        try:
            is_fully_completed = service_request.complete_request(request.user)
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
    template_name = "requests/request_complete_form.html"

    def get(self, request, pk):
        service_request = get_object_or_404(ServiceRequest, pk=pk)

        # Check if user has permission to complete this request
        if (
            request.user != service_request.service.provider
            and request.user != service_request.requester
        ):
            messages.error(
                request, "You do not have permission to complete this request."
            )
            return redirect("home")

        # Check if request is in a state that can be completed
        if service_request.status != "accepted":
            messages.error(request, "This request cannot be completed at this time.")
            return redirect("request_detail", pk=pk)

        # Check if user has already completed their part
        if (
            request.user == service_request.service.provider
            and service_request.provider_completed
        ):
            messages.error(
                request, "You have already marked this request as completed."
            )
            return redirect("request_detail", pk=pk)
        if (
            request.user == service_request.requester
            and service_request.requester_completed
        ):
            messages.error(
                request, "You have already confirmed this request as completed."
            )
            return redirect("request_detail", pk=pk)

        form = ServiceRequestCompleteForm(
            initial={"hours_completed": service_request.hours_requested}
        )
        return render(
            request, self.template_name, {"request": service_request, "form": form}
        )

    def post(self, request, pk):
        service_request = get_object_or_404(ServiceRequest, pk=pk)

        # Check if user has permission to complete this request
        if (
            request.user != service_request.service.provider
            and request.user != service_request.requester
        ):
            messages.error(
                request, "You do not have permission to complete this request."
            )
            return redirect("home")

        # Check if request is in a state that can be completed
        if service_request.status != "accepted":
            messages.error(request, "This request cannot be completed at this time.")
            return redirect("request_detail", pk=pk)

        # Check if user has already completed their part
        if (
            request.user == service_request.service.provider
            and service_request.provider_completed
        ):
            messages.error(
                request, "You have already marked this request as completed."
            )
            return redirect("request_detail", pk=pk)
        if (
            request.user == service_request.requester
            and service_request.requester_completed
        ):
            messages.error(
                request, "You have already confirmed this request as completed."
            )
            return redirect("request_detail", pk=pk)

        form = ServiceRequestCompleteForm(request.POST)
        if form.is_valid():
            action = request.POST.get("action")

            if action == "cancel":
                cancellation_reason = form.cleaned_data.get("cancellation_reason", "")
                service_request.reject_request(cancellation_reason)
                messages.success(request, "Request cancelled successfully!")
            else:  # complete
                hours_completed = form.cleaned_data["hours_completed"]
                try:
                    is_fully_completed = service_request.complete_request(
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
            request, self.template_name, {"request": service_request, "form": form}
        )


class RequestCommunityHoursView(LoginRequiredMixin, View):
    def get(self, request, pk):
        service_request = get_object_or_404(ServiceRequest, pk=pk)
        if not service_request.can_request_community_hours():
            messages.error(
                request, "This request cannot be converted to a community request."
            )
            return redirect("request_detail", pk=pk)
        return render(
            request,
            "requests/community_request_form.html",
            {"request": service_request},
        )

    def post(self, request, pk):
        service_request = get_object_or_404(ServiceRequest, pk=pk)
        if request.user != service_request.requester:
            messages.error(
                request, "Only the requester can convert to a community request."
            )
            return redirect("request_detail", pk=pk)

        if not service_request.can_request_community_hours():
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

        service_request.request_community_hours(reason)
        messages.success(request, "Community hours request submitted successfully!")
        return redirect("request_detail", pk=pk)


class ApproveCommunityRequestView(LoginRequiredMixin, UserPassesTestMixin, View):
    def get(self, request, pk):
        service_request = get_object_or_404(ServiceRequest, pk=pk)
        if not service_request.can_be_approved():
            messages.error(request, "This request cannot be approved.")
            return redirect("request_detail", pk=pk)
        return render(
            request,
            "requests/community_request_review.html",
            {"request": service_request},
        )

    def post(self, request, pk):
        service_request = get_object_or_404(ServiceRequest, pk=pk)
        if not service_request.can_be_approved():
            messages.error(request, "This request cannot be approved.")
            return redirect("request_detail", pk=pk)

        notes = request.POST.get("notes", "")
        try:
            service_request.approve_community_request(request.user, notes)
            messages.success(request, "Community hours request approved successfully!")
        except ValueError as e:
            messages.error(request, str(e))
        return redirect("request_detail", pk=pk)


class RejectCommunityRequestView(LoginRequiredMixin, UserPassesTestMixin, View):
    def get(self, request, pk):
        service_request = get_object_or_404(ServiceRequest, pk=pk)
        if not service_request.can_be_rejected():
            messages.error(request, "This request cannot be rejected.")
            return redirect("request_detail", pk=pk)
        return render(
            request,
            "requests/community_request_review.html",
            {"request": service_request},
        )

    def post(self, request, pk):
        service_request = get_object_or_404(ServiceRequest, pk=pk)
        if not service_request.can_be_rejected():
            messages.error(request, "This request cannot be rejected.")
            return redirect("request_detail", pk=pk)

        notes = request.POST.get("notes", "")
        service_request.reject_community_request(request.user, notes)
        messages.success(request, "Community hours request rejected.")
        return redirect("request_detail", pk=pk)

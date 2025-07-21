from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
    View,
)

from ..forms import (
    ServiceForm,
    ServiceTransactionCancelForm,
    ServiceTransactionCompleteForm,
    ServiceTransactionForm,
    ServiceTransactionRejectForm,
)
from ..models import Service, ServiceCategory, ServiceTransaction


class ServiceListView(ListView):
    model = Service
    template_name = "services/service_list.html"
    context_object_name = "services"

    def get_queryset(self):
        # Get category filter
        category_id = self.request.GET.get("category")
        category = None
        if category_id:
            try:
                category = ServiceCategory.objects.get(id=category_id)
            except (ServiceCategory.DoesNotExist, ValueError):
                pass

        # Get search filter
        search = self.request.GET.get("search", "")

        # Get view type filter
        view_type = self.request.GET.get("view", "public_services")

        # Show my services if the user is authenticated
        if view_type == "my_services" and self.request.user.is_authenticated:
            # Show all services offered by the current user (both active and inactive)
            services = Service.objects.filter(
                Q(title__icontains=search) | Q(description__icontains=search),
                provider=self.request.user,
                is_active=True,
                is_deleted=False,
            )
            if category:
                services = services.filter(category=category)
            return services
        else:
            # Show public services (including user's own services)
            return Service.get_active_services(
                category=category,
                search=search,
            )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "categories": ServiceCategory.get_all_categories(),
                "services": self.get_queryset(),
            }
        )
        return context


class ServiceCreateView(LoginRequiredMixin, CreateView):
    form_class = ServiceForm
    template_name = "services/service_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = ServiceCategory.get_all_categories()
        return context

    def form_valid(self, form):
        form.instance.provider = self.request.user
        messages.success(self.request, "Service created successfully!")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "There was an error creating the service.")
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse_lazy("service_detail", kwargs={"pk": self.object.pk})


class ServiceDetailView(DetailView):
    model = Service
    template_name = "services/service_detail.html"
    context_object_name = "service"


class ServiceDeleteView(LoginRequiredMixin, DeleteView):
    model = Service
    success_url = reverse_lazy("service_list")
    template_name = "services/service_confirm_delete.html"

    def get_queryset(self):
        return Service.objects.filter(provider=self.request.user)

    def post(self, request, *args, **kwargs):
        service: Service = self.get_object()

        # Check for any pending or accepted requests
        outstanding_requests = service.service_transactions.filter(
            status__in=["pending", "accepted"]
        ).exists()

        if outstanding_requests:
            messages.error(
                request,
                "Cannot delete service while there are pending or accepted requests. Please handle all outstanding requests first.",
            )
            return redirect("service_detail", pk=service.pk)

        # Soft delete the service
        service.is_deleted = True
        service.is_active = False  # Also deactivate it
        service.save()

        # Add success message and redirect
        messages.success(request, "Service deleted successfully.")
        return redirect(self.success_url)


class ServiceEditView(LoginRequiredMixin, UpdateView):
    model = Service
    form_class = ServiceForm
    template_name = "services/service_form.html"

    def get_object(self):
        return Service.objects.get(id=self.kwargs["pk"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = ServiceCategory.get_all_categories()
        return context

    def form_valid(self, form):
        messages.success(self.request, "Service updated successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("service_detail", kwargs={"pk": self.object.pk})


class ServiceTransactionView(LoginRequiredMixin, CreateView):
    form_class = ServiceTransactionForm
    template_name = "services/service_transaction_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["service"] = get_object_or_404(Service, pk=self.kwargs["pk"])
        return context

    def form_valid(self, form):
        form.instance.service = get_object_or_404(Service, pk=self.kwargs["pk"])
        form.instance.requester = self.request.user
        messages.success(self.request, "Service request submitted successfully!")
        return super().form_valid(form)

    def form_invalid(self, form):
        print(form.errors)
        messages.error(self.request, "There was an error submitting the request.")
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse_lazy("request_detail", kwargs={"pk": self.object.pk})


class ServiceTransactionDetailView(LoginRequiredMixin, DetailView):
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


class ServiceToggleActiveView(LoginRequiredMixin, View):
    def post(self, request, pk):
        service = get_object_or_404(Service, pk=pk, provider=request.user)

        # Check for any outstanding requests (pending or accepted)
        outstanding_requests = service.service_transactions.filter(
            status__in=["pending", "accepted"]
        ).exists()

        if outstanding_requests:
            messages.error(
                request,
                "Cannot deactivate service while there are outstanding requests. Please handle all pending and accepted requests first.",
            )
        else:
            service.is_active = not service.is_active
            service.save()
            status = "activated" if service.is_active else "deactivated"
            messages.success(request, f"Service has been {status} successfully.")

        return redirect("service_detail", pk=pk)


class ServiceTransactionAcceptView(LoginRequiredMixin, View):
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
        return redirect("service_detail", pk=pk)


class ServiceTransactionRejectView(LoginRequiredMixin, View):
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

        return redirect("service_detail", pk=pk)


class ServiceTransactionCancelView(LoginRequiredMixin, View):
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

        return redirect("service_detail", pk=pk)


class ServiceTransactionCompleteView(LoginRequiredMixin, View):
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

        return redirect("service_detail", pk=pk)


class ServiceTransactionCompleteFormView(LoginRequiredMixin, View):
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
            return redirect("service_detail", pk=pk)

        # Check if user has already completed their part
        if (
            request.user == service_transaction.service.provider
            and service_transaction.provider_completed
        ):
            messages.error(
                request, "You have already marked this request as completed."
            )
            return redirect("service_detail", pk=pk)
        if (
            request.user == service_transaction.requester
            and service_transaction.requester_completed
        ):
            messages.error(
                request, "You have already confirmed this request as completed."
            )
            return redirect("service_detail", pk=pk)

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
            return redirect("service_detail", pk=pk)

        # Check if user has already completed their part
        if (
            request.user == service_transaction.service.provider
            and service_transaction.provider_completed
        ):
            messages.error(
                request, "You have already marked this request as completed."
            )
            return redirect("service_detail", pk=pk)
        if (
            request.user == service_transaction.requester
            and service_transaction.requester_completed
        ):
            messages.error(
                request, "You have already confirmed this request as completed."
            )
            return redirect("service_detail", pk=pk)

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
                return redirect("service_detail", pk=pk)

            return redirect("service_detail", pk=pk)

        return render(
            request, self.template_name, {"request": service_transaction, "form": form}
        )


class ServiceTransactionCommunityHoursView(LoginRequiredMixin, View):
    def get(self, request, pk):
        service_transaction = get_object_or_404(ServiceTransaction, pk=pk)
        if not service_transaction.can_request_community_hours():
            messages.error(
                request, "This request cannot be converted to a community request."
            )
            return redirect("service_detail", pk=pk)
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
            return redirect("service_detail", pk=pk)

        if not service_transaction.can_request_community_hours():
            messages.error(
                request, "This request cannot be converted to a community request."
            )
            return redirect("service_detail", pk=pk)

        reason = request.POST.get("reason", "")
        if not reason:
            messages.error(
                request, "Please provide a reason for requesting community hours."
            )
            return redirect("service_detail", pk=pk)

        service_transaction.request_community_hours(reason)
        messages.success(request, "Community hours request submitted successfully!")
        return redirect("service_detail", pk=pk)


class ServiceTransactionCommunityHoursApproveView(LoginRequiredMixin, View):
    def get(self, request, pk):
        service_transaction = get_object_or_404(ServiceTransaction, pk=pk)
        if not service_transaction.can_be_approved():
            messages.error(request, "This request cannot be approved.")
            return redirect("service_detail", pk=pk)
        return render(
            request,
            "requests/community_request_review.html",
            {"request": service_transaction},
        )

    def post(self, request, pk):
        service_transaction = get_object_or_404(ServiceTransaction, pk=pk)
        if not service_transaction.can_be_approved():
            messages.error(request, "This request cannot be approved.")
            return redirect("service_detail", pk=pk)

        notes = request.POST.get("notes", "")
        try:
            service_transaction.approve_community_request(request.user, notes)
            messages.success(request, "Community hours request approved successfully!")
        except ValueError as e:
            messages.error(request, str(e))
        return redirect("service_detail", pk=pk)


class ServiceTransactionCommunityHoursRejectView(LoginRequiredMixin, View):
    def get(self, request, pk):
        service_transaction = get_object_or_404(ServiceTransaction, pk=pk)
        if not service_transaction.can_be_rejected():
            messages.error(request, "This request cannot be rejected.")
            return redirect("service_detail", pk=pk)
        return render(
            request,
            "requests/community_request_review.html",
            {"request": service_transaction},
        )

    def post(self, request, pk):
        service_transaction = get_object_or_404(ServiceTransaction, pk=pk)
        if not service_transaction.can_be_rejected():
            messages.error(request, "This request cannot be rejected.")
            return redirect("service_detail", pk=pk)

        notes = request.POST.get("notes", "")
        service_transaction.reject_community_request(request.user, notes)
        messages.success(request, "Community hours request rejected.")
        return redirect("service_detail", pk=pk)

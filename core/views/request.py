from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q, Count, F
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DetailView,
    ListView,
    UpdateView,
    View,
)

from ..forms import (
    RequestForm,
    RequestTransactionForm,
    RequestTransactionCompleteForm,
    RequestTransactionRejectForm,
    RequestTransactionCancelForm,
)
from ..models import Request, RequestTransaction, ServiceTransaction, ServiceCategory


class UserRequestListView(LoginRequiredMixin, ListView):
    model = ServiceTransaction
    template_name = "my_requests/request_list.html"
    context_object_name = "requests"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get status parameters for each column
        by_me_status = self.request.GET.get("by_me_status")
        to_me_status = self.request.GET.get("to_me_status")
        my_offers_status = self.request.GET.get("my_offers_status")

        # Base querysets for each column
        my_requests = ServiceTransaction.objects.filter(requester=self.request.user)
        requests_to_me = ServiceTransaction.objects.filter(
            service__provider=self.request.user
        )

        # Get RequestTransactions (offers made by this user to help with requests)
        my_offers = RequestTransaction.objects.filter(provider=self.request.user)

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

        # Apply status filters for my offers
        if my_offers_status:
            if my_offers_status == "active":
                my_offers = my_offers.filter(status__in=["pending", "accepted"])
            elif my_offers_status == "closed":
                my_offers = my_offers.filter(status__in=["rejected", "canceled"])
            else:
                my_offers = my_offers.filter(status=my_offers_status)
        else:
            # Default to active offers if no status specified
            my_offers = my_offers.filter(status__in=["pending", "accepted"])

        # Order all querysets
        context["my_requests"] = my_requests.order_by("-created_at")
        context["requests_to_me"] = requests_to_me.order_by("-created_at")
        context["my_offers"] = my_offers.order_by("-created_at")

        return context


class RequestDetailView(LoginRequiredMixin, DetailView):
    model = Request
    template_name = "requests/request_detail.html"
    context_object_name = "request"

    def get_object(self):
        obj = super().get_object()
        # Community requests can be viewed by anyone who is logged in
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get all offers for this request
        context["offers"] = RequestTransaction.objects.filter(
            request=self.object
        ).order_by("-created_at")

        # Add information about whether the request is fully staffed
        context["is_fully_staffed"] = self.object.is_fully_staffed
        context["accepted_offers_count"] = self.object.accepted_offers_count

        return context


class RequestCreateView(LoginRequiredMixin, CreateView):
    form_class = RequestForm
    template_name = "requests/request_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = ServiceCategory.objects.all().order_by("name")
        return context

    def form_valid(self, form):
        form.instance.requester = self.request.user
        messages.success(self.request, "Community request created successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("request_detail", kwargs={"pk": self.object.pk})


class RequestListView(LoginRequiredMixin, ListView):
    model = Request
    template_name = "requests/request_list.html"
    context_object_name = "requests"
    paginate_by = 20

    def get_queryset(self):
        """Get requests based on view type (public_requests or my_requests)."""
        # Get search filter
        search = self.request.GET.get("search", "")

        # Get view type filter
        view_type = self.request.GET.get("view", "public_requests")

        # Show my requests if the user is authenticated and view is my_requests
        if view_type == "my_requests" and self.request.user.is_authenticated:
            # Show all requests created by the current user (both active and inactive)
            queryset = Request.objects.filter(
                Q(title__icontains=search) | Q(description__icontains=search),
                requester=self.request.user,
                is_active=True,
                is_deleted=False,
            )
        else:
            # Show public requests (excluding user's own requests)
            queryset = Request.get_active_requests(exclude_user=self.request.user)

            # Apply search filter
            if search:
                queryset = queryset.filter(
                    Q(title__icontains=search) | Q(description__icontains=search)
                )

            # Exclude fully staffed requests for public view
            queryset = queryset.exclude(
                id__in=Request.objects.filter(
                    is_active=True,
                    is_deleted=False
                ).annotate(
                    accepted_count=Count('offers', filter=Q(offers__status='accepted'))
                ).filter(
                    accepted_count__gte=F('num_users_needed')
                ).values_list('id', flat=True)
            )

        # Apply category filter if provided
        category = self.request.GET.get("category")
        if category:
            queryset = queryset.filter(category__name=category)

        # Apply priority filter if provided
        priority = self.request.GET.get("priority")
        if priority:
            queryset = queryset.filter(urgency=priority)

        # Annotate with staffing information
        queryset = queryset.annotate(
            accepted_count=Count('offers', filter=Q(offers__status='accepted'))
        )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from ..models import ServiceCategory

        # Add categories for filtering
        context["categories"] = ServiceCategory.objects.all().order_by("name")

        # Add search and filter parameters
        context["current_category"] = self.request.GET.get("category")
        context["current_priority"] = self.request.GET.get("priority")
        context["current_search"] = self.request.GET.get("search")
        context["current_view"] = self.request.GET.get("view", "public_requests")

        return context


class RequestEditView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Request
    form_class = RequestForm
    template_name = "requests/request_form.html"

    def test_func(self):
        request_obj: Request = self.get_object()
        return self.request.user == request_obj.requester

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = ServiceCategory.objects.all().order_by("name")
        context["request_obj"] = self.object  # Pass the request object for edit mode
        return context

    def get_success_url(self):
        return reverse_lazy("request_detail", kwargs={"pk": self.object.pk})


class RequestToggleActiveView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        request_obj = get_object_or_404(Request, pk=self.kwargs["pk"])
        return self.request.user == request_obj.requester

    def post(self, request, pk):
        request_obj = get_object_or_404(Request, pk=pk)
        request_obj.is_active = not request_obj.is_active
        request_obj.save()

        status = "activated" if request_obj.is_active else "deactivated"
        messages.success(request, f"Request {status} successfully!")

        return redirect("request_detail", pk=pk)


class RequestDeleteView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        request_obj = get_object_or_404(Request, pk=self.kwargs["pk"])
        return self.request.user == request_obj.requester

    def post(self, request, pk):
        request_obj = get_object_or_404(Request, pk=pk)
        request_obj.delete()
        messages.success(request, "Request deleted successfully!")
        return redirect("request_list")


class RequestTransactionView(LoginRequiredMixin, CreateView):
    form_class = RequestTransactionForm
    template_name = "requests/request_transaction_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["request"] = get_object_or_404(Request, pk=self.kwargs["pk"])
        return context

    def form_valid(self, form):
        form.instance.request = get_object_or_404(Request, pk=self.kwargs["pk"])
        form.instance.provider = self.request.user
        messages.success(self.request, "Offer submitted successfully!")
        return super().form_valid(form)

    def form_invalid(self, form):
        print(form.errors)
        messages.error(self.request, "There was an error submitting the offer.")
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse_lazy("request_detail", kwargs={"pk": self.kwargs["pk"]})


class RequestTransactionAcceptView(LoginRequiredMixin, View):
    def post(self, request, pk):
        request_transaction = get_object_or_404(RequestTransaction, pk=pk)
        if request.user != request_transaction.request.requester:
            messages.error(request, "Only the request owner can accept offers.")
            return redirect("home")

        try:
            request_transaction.accept_offer()
            messages.success(request, "Offer accepted successfully!")
        except ValueError as e:
            messages.error(request, str(e))

        return redirect("request_detail", pk=request_transaction.request.pk)


class RequestTransactionRejectView(LoginRequiredMixin, View):
    def post(self, request, pk):
        request_transaction = get_object_or_404(RequestTransaction, pk=pk)
        if request.user != request_transaction.request.requester:
            messages.error(request, "Only the request owner can reject offers.")
            return redirect("home")

        form = RequestTransactionRejectForm(request.POST)
        if form.is_valid():
            try:
                rejection_reason = form.cleaned_data["rejection_reason"]
                request_transaction.reject_offer(rejection_reason)
                messages.success(request, "Offer rejected successfully!")
            except ValueError as e:
                messages.error(request, str(e))
        else:
            messages.error(
                request, "Please provide a reason for rejecting the offer."
            )

        return redirect("request_detail", pk=request_transaction.request.pk)


class RequestTransactionCancelView(LoginRequiredMixin, View):
    def post(self, request, pk):
        request_transaction = get_object_or_404(RequestTransaction, pk=pk)
        if request.user != request_transaction.provider:
            messages.error(request, "Only the offer provider can cancel offers.")
            return redirect("home")

        form = RequestTransactionCancelForm(request.POST)
        if form.is_valid():
            try:
                cancellation_reason = form.cleaned_data.get("cancellation_reason", "")
                request_transaction.cancel_offer(cancellation_reason)
                messages.success(request, "Offer canceled successfully!")
            except ValueError as e:
                messages.error(request, str(e))
        else:
            messages.error(request, "There was an error processing your request.")

        return redirect("request_detail", pk=request_transaction.request.pk)


class RequestTransactionCompleteFormView(LoginRequiredMixin, View):
    template_name = "requests/request_transaction_complete_form.html"

    def get(self, request, pk):
        request_transaction = get_object_or_404(RequestTransaction, pk=pk)

        # Check if user has permission to complete this offer
        if (
            request.user != request_transaction.provider
            and request.user != request_transaction.request.requester
        ):
            messages.error(
                request, "You do not have permission to complete this offer."
            )
            return redirect("home")

        # Check if offer is in a state that can be completed
        if request_transaction.status != "accepted":
            messages.error(request, "This offer cannot be completed at this time.")
            return redirect("request_detail", pk=request_transaction.request.pk)

        # Check if user has already completed their part
        if (
            request.user == request_transaction.provider
            and request_transaction.provider_completed
        ):
            messages.error(
                request, "You have already marked this offer as completed."
            )
            return redirect("request_detail", pk=request_transaction.request.pk)
        if (
            request.user == request_transaction.request.requester
            and request_transaction.requester_completed
        ):
            messages.error(
                request, "You have already confirmed this offer as completed."
            )
            return redirect("request_detail", pk=request_transaction.request.pk)

        form = RequestTransactionCompleteForm(
            initial={"hours_completed": request_transaction.proposed_hours}
        )
        return render(
            request, self.template_name, {"offer": request_transaction, "form": form}
        )

    def post(self, request, pk):
        request_transaction = get_object_or_404(RequestTransaction, pk=pk)

        # Check if user has permission to complete this offer
        if (
            request.user != request_transaction.provider
            and request.user != request_transaction.request.requester
        ):
            messages.error(
                request, "You do not have permission to complete this offer."
            )
            return redirect("home")

        # Check if offer is in a state that can be completed
        if request_transaction.status != "accepted":
            messages.error(request, "This offer cannot be completed at this time.")
            return redirect("request_detail", pk=request_transaction.request.pk)

        # Check if user has already completed their part
        if (
            request.user == request_transaction.provider
            and request_transaction.provider_completed
        ):
            messages.error(
                request, "You have already marked this offer as completed."
            )
            return redirect("request_detail", pk=request_transaction.request.pk)
        if (
            request.user == request_transaction.request.requester
            and request_transaction.requester_completed
        ):
            messages.error(
                request, "You have already confirmed this offer as completed."
            )
            return redirect("request_detail", pk=request_transaction.request.pk)

        form = RequestTransactionCompleteForm(request.POST)
        if form.is_valid():
            hours_completed = form.cleaned_data["hours_completed"]
            try:
                is_fully_completed = request_transaction.complete_offer(
                    request.user, hours_completed=hours_completed
                )
                if is_fully_completed:
                    messages.success(
                        request,
                        "Offer completed successfully! Time credits have been transferred.",
                    )
                else:
                    messages.success(
                        request,
                        "Completion status updated. Waiting for the other party to complete.",
                    )
            except ValueError as e:
                messages.error(request, str(e))
                return redirect("request_detail", pk=request_transaction.request.pk)

            return redirect("request_detail", pk=request_transaction.request.pk)

        return render(
            request, self.template_name, {"offer": request_transaction, "form": form}
        )

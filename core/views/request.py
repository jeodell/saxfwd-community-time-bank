from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DetailView,
    ListView,
    UpdateView,
    View,
)

from ..forms import RequestTransactionForm
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
    model = Request
    template_name = "requests/request_detail.html"
    context_object_name = "request"

    def get_object(self):
        obj = super().get_object()
        # Community requests can be viewed by anyone who is logged in
        return obj


class RequestCreateView(LoginRequiredMixin, CreateView):
    model = Request
    template_name = "requests/request_form.html"
    fields = [
        "title",
        "description",
        "category",
        "preferred_date",
        "estimated_hours",
        "num_users_needed",
        "urgency",
    ]

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
        """Get active community requests, excluding the current user's own requests."""
        queryset = Request.get_active_requests(exclude_user=self.request.user)

        # Apply category filter if provided
        category = self.request.GET.get("category")
        if category:
            queryset = queryset.filter(category__name=category)

        # Apply priority filter if provided
        priority = self.request.GET.get("priority")
        if priority:
            queryset = queryset.filter(urgency=priority)

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
        context["current_priority"] = self.request.GET.get("priority")
        context["current_search"] = self.request.GET.get("search")

        return context


class RequestEditView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Request
    template_name = "requests/request_form.html"
    fields = [
        "title",
        "description",
        "category",
        "preferred_date",
        "estimated_hours",
        "num_users_needed",
        "urgency",
    ]

    def test_func(self):
        request_obj = self.get_object()
        return self.request.user == request_obj.requester

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

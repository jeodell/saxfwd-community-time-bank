from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
    View,
)

from ..forms import ServiceForm, ServiceRequestForm
from ..models import Service, ServiceCategory


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
        view_type = self.request.GET.get("view", "public")

        # Show offered services if the user is authenticated
        if view_type == "offered" and self.request.user.is_authenticated:
            # Show only active services offered by the current user
            services = Service.objects.filter(
                Q(title__icontains=search) | Q(description__icontains=search),
                provider=self.request.user,
                is_active=True,  # Only show active services
            )
            if category:
                services = services.filter(category=category)
            return services
        else:
            # Show public services (excluding user's own services)
            return Service.get_active_services(
                exclude_user=self.request.user
                if self.request.user.is_authenticated
                else None,
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

    def get_success_url(self):
        return reverse_lazy("service_detail", kwargs={"pk": self.object.pk})


class ServiceRequestView(LoginRequiredMixin, CreateView):
    form_class = ServiceRequestForm
    template_name = "requests/request_form.html"

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


class ServiceToggleActiveView(LoginRequiredMixin, View):
    def post(self, request, pk):
        service = get_object_or_404(Service, pk=pk, provider=request.user)

        # Check for any outstanding requests (pending or accepted)
        outstanding_requests = service.servicerequest_set.filter(
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

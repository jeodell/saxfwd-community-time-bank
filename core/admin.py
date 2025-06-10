from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import (
    Service,
    ServiceCategory,
    ServiceRequest,
    TimeBankLedger,
    User,
)


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "description", "is_featured")
    search_fields = ("name",)


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "provider",
        "category",
        "is_active",
        "created_at",
    )
    list_filter = ("category", "is_active", "created_at")
    search_fields = (
        "title",
        "description",
        "provider__first_name",
        "provider__last_name",
    )
    date_hierarchy = "created_at"


@admin.register(ServiceRequest)
class ServiceRequestAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "service",
        "requester",
        "status",
        "requested_date",
        "hours_requested",
        "hours_completed",
        "provider_completed",
        "requester_completed",
        "completed_at",
        "created_at",
    )
    list_filter = (
        "status",
        "requested_date",
        "created_at",
        "provider_completed",
        "requester_completed",
    )
    search_fields = (
        "service__title",
        "requester__first_name",
        "requester__last_name",
        "description",
    )
    date_hierarchy = "created_at"
    readonly_fields = ("created_at", "updated_at", "completed_at")
    fieldsets = (
        (
            "Service Information",
            {
                "fields": (
                    "service",
                    "requester",
                    "hours_requested",
                    "hours_completed",
                    "description",
                )
            },
        ),
        (
            "Request Status",
            {
                "fields": (
                    "status",
                    "requested_date",
                    "provider_completed",
                    "requester_completed",
                    "completed_at",
                )
            },
        ),
        (
            "System Information",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(TimeBankLedger)
class TimeBankLedgerAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "service_request",
        "transaction_type",
        "hours",
        "balance",
        "created_at",
    )
    list_filter = ("transaction_type", "created_at")
    search_fields = (
        "user__email",
        "user__first_name",
        "user__last_name",
        "description",
    )
    date_hierarchy = "created_at"


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ("email",)
    list_display = (
        "id",
        "email",
        "first_name",
        "last_name",
        "phone_number",
        "address",
        "total_hours_earned",
        "total_hours_spent",
        "is_staff",
        "is_superuser",
        "is_active",
        "date_joined",
        "updated_at",
    )
    list_filter = ("is_active", "is_staff", "is_superuser")
    search_fields = (
        "email",
        "first_name",
        "last_name",
        "phone_number",
        "address",
    )
    readonly_fields = (
        "total_hours_earned",
        "total_hours_spent",
        "date_joined",
        "updated_at",
    )
    fieldsets = (
        (
            "User Information",
            {
                "fields": (
                    "email",
                    "password",
                    "first_name",
                    "last_name",
                    "phone_number",
                    "address",
                    "bio",
                    "image",
                )
            },
        ),
        (
            "Time Bank Status",
            {
                "fields": (
                    "total_hours_earned",
                    "total_hours_spent",
                )
            },
        ),
        (
            "System Information",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "date_joined",
                    "updated_at",
                ),
            },
        ),
    )

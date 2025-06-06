from django.contrib import admin

from .models import (
    Service,
    ServiceCategory,
    ServiceRequest,
    TimeBankLedger,
    UserProfile,
)


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "is_featured")
    search_fields = ("name",)


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "provider",
        "category",
        "is_active",
        "created_at",
    )
    list_filter = ("category", "is_active", "created_at")
    search_fields = ("title", "description", "provider__username")
    date_hierarchy = "created_at"


@admin.register(ServiceRequest)
class ServiceRequestAdmin(admin.ModelAdmin):
    list_display = (
        "service",
        "requester",
        "status",
        "requested_date",
        "hours_requested",
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
    search_fields = ("service__title", "requester__username", "description")
    date_hierarchy = "created_at"
    readonly_fields = ("created_at", "updated_at", "completed_at")
    fieldsets = (
        (
            "Service Information",
            {"fields": ("service", "requester", "hours_requested", "description")},
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
        "user",
        "service_request",
        "transaction_type",
        "hours",
        "balance",
        "created_at",
    )
    list_filter = ("transaction_type", "created_at")
    search_fields = ("user__username", "description")
    date_hierarchy = "created_at"


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "is_active",
        "total_hours_earned",
        "total_hours_spent",
        "created_at",
        "updated_at",
    )
    list_filter = ("is_active", "created_at")
    search_fields = ("user__username", "bio", "phone_number", "email", "address")
    readonly_fields = (
        "is_active",
        "total_hours_earned",
        "total_hours_spent",
        "created_at",
        "updated_at",
    )
    fieldsets = (
        (
            "User Information",
            {"fields": ("user", "image", "bio", "phone_number", "email", "address")},
        ),
        (
            "Time Bank Status",
            {"fields": ("is_active", "total_hours_earned", "total_hours_spent")},
        ),
        (
            "System Information",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

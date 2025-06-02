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
    list_display = ("name", "description")
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
        "created_at",
    )
    list_filter = ("status", "requested_date", "created_at")
    search_fields = ("service__title", "requester__username", "description")
    date_hierarchy = "created_at"


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
        "total_hours_earned",
        "total_hours_spent",
        "balance",
        "rating",
    )
    search_fields = ("user__username", "bio", "phone_number")
    readonly_fields = ("total_hours_earned", "total_hours_spent", "rating")

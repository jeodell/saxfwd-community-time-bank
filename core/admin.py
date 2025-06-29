from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import (
    MeetingNotes,
    Service,
    ServiceCategory,
    ServiceRequest,
    TimeBankLedger,
    User,
)


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    ordering = ("name",)
    list_display = ("name", "description", "is_featured", "created_at")
    search_fields = (
        "id",
        "name",
    )
    date_hierarchy = "created_at"


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    ordering = ("-created_at",)
    list_display = (
        "title",
        "provider",
        "category",
        "is_active",
        "created_at",
    )
    list_filter = ("category", "is_active", "created_at")
    search_fields = (
        "id",
        "title",
        "description",
        "provider__first_name",
        "provider__last_name",
    )
    date_hierarchy = "created_at"


@admin.register(ServiceRequest)
class ServiceRequestAdmin(admin.ModelAdmin):
    ordering = ("-created_at",)
    list_display = (
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
        "id",
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
                    "cancellation_reason",
                    "rejection_reason",
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
    ordering = ("-created_at",)
    list_display = (
        "user",
        "service_request",
        "transaction_type",
        "hours",
        "created_at",
    )
    list_filter = ("transaction_type", "created_at")
    search_fields = (
        "user__id",
        "user__email",
        "user__first_name",
        "user__last_name",
        "description",
    )
    date_hierarchy = "created_at"


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ("-date_joined",)
    list_display = (
        "email",
        "first_name",
        "last_name",
        "phone_number",
        "address",
        "total_hours_earned",
        "total_hours_spent",
        "time_balance",
        "is_staff",
        "is_superuser",
        "is_active",
        "date_joined",
        "updated_at",
    )
    list_filter = ("is_active", "is_staff", "is_superuser")
    search_fields = (
        "id",
        "email",
        "first_name",
        "last_name",
        "phone_number",
        "address",
    )
    readonly_fields = (
        "total_hours_earned",
        "total_hours_spent",
        "time_balance",
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
                    "time_balance",
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


@admin.register(MeetingNotes)
class MeetingNotesAdmin(admin.ModelAdmin):
    list_display = ["meeting_date", "is_public", "created_by", "created_at"]
    list_filter = ["meeting_date", "is_public", "created_at"]
    date_hierarchy = "meeting_date"
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        ("Meeting Information", {"fields": ("meeting_date",)}),
        ("File Upload", {"fields": ("pdf_file",)}),
        ("Settings", {"fields": ("is_public", "created_by")}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def save_model(self, request, obj, form, change):
        if not change:  # Only set created_by on creation
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

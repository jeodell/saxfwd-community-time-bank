from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import (
    Application,
    CommunityHours,
    MeetingNotes,
    Request,
    RequestTransaction,
    Service,
    ServiceCategory,
    ServiceTransaction,
    TimeBankLedger,
    User,
)
from .views.base import send_approval_email


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


@admin.register(ServiceTransaction)
class ServiceTransactionAdmin(admin.ModelAdmin):
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

    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of service transactions for audit purposes
        return False


@admin.register(TimeBankLedger)
class TimeBankLedgerAdmin(admin.ModelAdmin):
    ordering = ("-created_at",)
    list_display = (
        "user",
        "service_transaction",
        "request_transaction",
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
    readonly_fields = ("created_at",)

    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of ledger entries for audit purposes
        return False


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
    list_filter = (
        "is_active",
        "is_staff",
        "is_superuser",
    )
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

    def save_model(self, request, obj, form, change):
        """Override save_model to send approval email when user becomes fully approved."""
        if change:  # Only for existing users
            try:
                old_obj = User.objects.get(pk=obj.pk)
                # Check if user just became fully approved
                if not old_obj.is_fully_approved and obj.is_fully_approved:
                    # Send approval email
                    send_approval_email(obj)
            except User.DoesNotExist:
                pass

        super().save_model(request, obj, form, change)


@admin.register(MeetingNotes)
class MeetingNotesAdmin(admin.ModelAdmin):
    list_display = ["meeting_date", "created_at"]
    list_filter = ["meeting_date", "created_at"]
    date_hierarchy = "meeting_date"
    readonly_fields = ["created_at"]

    fieldsets = (
        ("Meeting Information", {"fields": ("meeting_date",)}),
        ("File Upload", {"fields": ("pdf_file",)}),
        (
            "Timestamps",
            {"fields": ("created_at",), "classes": ("collapse",)},
        ),
    )


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = (
        "user_full_name",
        "email",
        "status",
        "referral_approved_by",
        "referral_approved_at",
        "referral_member_name",
        "is_referral_approved",
        "onboarded_at",
        "is_onboarded",
        "created_at",
        "updated_at",
    )
    list_filter = ("status", "created_at")
    search_fields = (
        "user__first_name",
        "user__last_name",
        "user__email",
        "referral_member__first_name",
        "referral_member__last_name",
        "writeup",
    )
    readonly_fields = (
        "user_full_name",
        "email",
        "created_at",
        "updated_at",
    )
    fieldsets = (
        (
            "Applicant Information",
            {
                "fields": (
                    "user",
                    "user_full_name",
                    "email",
                    "referral_member",
                    "writeup",
                )
            },
        ),
        (
            "Review Information",
            {
                "fields": (
                    "status",
                    "referral_approved_by",
                    "referral_approved_at",
                    "is_referral_approved",
                    "onboarded_at",
                    "is_onboarded",
                )
            },
        ),
        (
            "Timestamps",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )
    actions = ["approve_applications", "reject_applications"]

    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of applications for audit purposes
        return False

    def user_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"

    user_full_name.short_description = "Applicant Name"

    def email(self, obj):
        return obj.user.email

    email.short_description = "Email"

    def referral_member_name(self, obj):
        if obj.referral_member:
            return f"{obj.referral_member.first_name} {obj.referral_member.last_name}"
        return "No referral"

    referral_member_name.short_description = "Referral Member"

    def approve_applications(self, request, queryset):
        count = 0
        for application in queryset.filter(status="pending"):
            application.approve(request.user)
            count += 1
        self.message_user(request, f"Successfully approved {count} application(s).")

    approve_applications.short_description = "Approve selected applications"

    def reject_applications(self, request, queryset):
        count = 0
        for application in queryset.filter(status="pending"):
            application.reject(request.user)
            count += 1
        self.message_user(request, f"Successfully rejected {count} application(s).")

    reject_applications.short_description = "Reject selected applications"


@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    ordering = ("-created_at",)
    list_display = (
        "title",
        "requester",
        "category",
        "priority",
        "estimated_hours",
        "num_users_needed",
        "is_active",
        "created_at",
    )
    list_filter = ("category", "priority", "is_active", "created_at")
    search_fields = (
        "id",
        "title",
        "description",
        "requester__first_name",
        "requester__last_name",
    )
    date_hierarchy = "created_at"


@admin.register(RequestTransaction)
class RequestTransactionAdmin(admin.ModelAdmin):
    ordering = ("-created_at",)
    list_display = (
        "request",
        "provider",
        "status",
        "proposed_hours",
        "hours_completed",
        "provider_completed",
        "requester_completed",
        "completed_at",
        "created_at",
    )
    list_filter = (
        "status",
        "created_at",
        "provider_completed",
        "requester_completed",
    )
    search_fields = (
        "id",
        "request__title",
        "provider__first_name",
        "provider__last_name",
        "message",
    )
    date_hierarchy = "created_at"
    readonly_fields = ("created_at", "updated_at", "completed_at")
    fieldsets = (
        (
            "Request Information",
            {
                "fields": (
                    "request",
                    "provider",
                    "proposed_hours",
                    "hours_completed",
                    "message",
                )
            },
        ),
        (
            "Offer Status",
            {
                "fields": (
                    "status",
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

    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of request transactions for audit purposes
        return False


@admin.register(CommunityHours)
class CommunityHoursAdmin(admin.ModelAdmin):
    list_display = ("total_hours", "created_at", "updated_at")
    readonly_fields = ("total_hours", "created_at", "updated_at")

    def has_add_permission(self, request):
        # Only allow one instance
        return not CommunityHours.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # Don't allow deletion of the community hours instance
        return False

    fieldsets = (
        (
            "Community Hours Balance",
            {
                "fields": ("total_hours",),
                "description": "This balance is calculated automatically from ledger entries (donations - requests)."
            },
        ),
        (
            "System Information",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

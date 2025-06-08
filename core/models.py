from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone


class ServiceCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_featured = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Service Categories"

    @classmethod
    def get_featured_categories(cls):
        """Get all featured categories ordered by name."""
        return cls.objects.filter(is_featured=True).order_by("name")

    @classmethod
    def get_all_categories(cls):
        """Get all categories ordered by name."""
        return cls.objects.all().order_by("name")


class Service(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    provider = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="services_provided"
    )
    category = models.ForeignKey(ServiceCategory, on_delete=models.SET_NULL, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} by {self.provider.username}"

    def can_be_edited_by(self, user):
        """Check if the service can be edited by the given user."""
        return user == self.provider

    @classmethod
    def get_active_services(cls, exclude_user=None, category=None, search=None):
        """
        Get active services with optional filtering.

        Args:
            exclude_user: User whose services should be excluded
            category: Category name to filter by
            search: Search term to filter by title or description
        """
        queryset = cls.objects.filter(is_active=True)

        if exclude_user:
            queryset = queryset.exclude(provider=exclude_user)

        if category:
            queryset = queryset.filter(category__name=category)

        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )

        return queryset


class ServiceRequest(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    COMMUNITY_REQUEST_STATUS = [
        ("not_requested", "Not Requested"),
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    requester = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="service_requests"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    requested_date = models.DateTimeField()
    hours_requested = models.DecimalField(
        max_digits=5, decimal_places=2, validators=[MinValueValidator(0.5)]
    )
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    provider_completed = models.BooleanField(default=False)
    requester_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Community hours request fields
    is_community_request = models.BooleanField(default=False)
    community_request_status = models.CharField(
        max_length=20, choices=COMMUNITY_REQUEST_STATUS, default="not_requested"
    )
    community_request_reason = models.TextField(
        blank=True, help_text="Please explain why you need community hours"
    )
    community_request_reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_community_requests",
    )
    community_request_review_notes = models.TextField(blank=True)
    community_request_reviewed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.service.title} request by {self.requester.username}"

    class Meta:
        verbose_name_plural = "Service Requests"

    def request_community_hours(self, reason):
        """
        Convert this service request to a community hours request.
        """
        if self.is_community_request:
            raise ValueError("This request is already a community request")

        self.is_community_request = True
        self.community_request_status = "pending"
        self.community_request_reason = reason
        self.save()

    def approve_community_request(self, reviewer, notes=""):
        """
        Approve a community hours request and deduct hours from the community timebank.
        """
        if not self.is_community_request:
            raise ValueError("This is not a community request")

        if self.community_request_status != "pending":
            raise ValueError("This request is not pending approval")

        # Get the community timebank
        community_bank, _ = CommunityHours.objects.get_or_create()

        # Check if we have enough hours
        if not community_bank.deduct_hours(self.hours_requested):
            raise ValueError("Insufficient community hours available")

        # Update the request
        self.community_request_status = "approved"
        self.community_request_reviewed_by = reviewer
        self.community_request_review_notes = notes
        self.community_request_reviewed_at = timezone.now()
        self.save()

        # Create a ledger entry for the community hours usage
        TimeBankLedger.objects.create(
            user=self.requester,
            service_request=self,
            transaction_type="community_request",
            hours=self.hours_requested,
            balance=self.requester.userprofile.time_balance,
            description=f"Community hours used for {self.service.title}",
        )

    def reject_community_request(self, reviewer, notes=""):
        """
        Reject a community hours request.
        """
        if not self.is_community_request:
            raise ValueError("This is not a community request")

        if self.community_request_status != "pending":
            raise ValueError("This request is not pending approval")

        self.community_request_status = "rejected"
        self.community_request_reviewed_by = reviewer
        self.community_request_review_notes = notes
        self.community_request_reviewed_at = timezone.now()
        self.save()

    def can_request_community_hours(self):
        """Check if this request can be converted to a community request."""
        return not self.is_community_request and self.status == "pending"

    def can_be_approved(self):
        """Check if this community request can be approved."""
        return (
            self.is_community_request
            and self.community_request_status == "pending"
            and self.status == "pending"
        )

    def can_be_rejected(self):
        """Check if this community request can be rejected."""
        return (
            self.is_community_request
            and self.community_request_status == "pending"
            and self.status == "pending"
        )

    def accept_request(self):
        """
        Accept this service request.
        """
        if self.status != "pending":
            raise ValueError("This request cannot be accepted")

        self.status = "accepted"
        self.save()

    def reject_request(self):
        """
        Reject this service request.
        """
        if self.status != "pending":
            raise ValueError("This request cannot be rejected")

        self.status = "rejected"
        self.save()

    def complete_request(self, user):
        """
        Mark this request as complete by either the provider or requester.
        Returns True if both parties have completed, False otherwise.
        """
        if self.status != "accepted":
            raise ValueError("This request cannot be completed")

        if user == self.service.provider:
            self.provider_completed = True
        elif user == self.requester:
            self.requester_completed = True
        else:
            raise ValueError("Only the provider or requester can complete this request")

        if self.provider_completed and self.requester_completed:
            self.status = "completed"
            self.completed_at = timezone.now()

            # Update timebank ledger
            hours = self.hours_requested
            provider_profile = UserProfile.objects.get_or_create(
                user=self.service.provider
            )[0]
            requester_profile = UserProfile.objects.get_or_create(user=self.requester)[
                0
            ]

            # Credit provider
            TimeBankLedger.objects.create(
                user=self.service.provider,
                service_request=self,
                transaction_type="credit",
                hours=hours,
                balance=provider_profile.total_hours_earned + hours,
                description=f"Completed service: {self.service.title}",
            )
            provider_profile.total_hours_earned += hours
            provider_profile.save()

            # Debit requester
            TimeBankLedger.objects.create(
                user=self.requester,
                service_request=self,
                transaction_type="debit",
                hours=hours,
                balance=requester_profile.total_hours_spent + hours,
                description=f"Received service: {self.service.title}",
            )
            requester_profile.total_hours_spent += hours
            requester_profile.save()

        self.save()
        return self.provider_completed and self.requester_completed


class CommunityHours(models.Model):
    total_hours = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Community Time Bank: {self.total_hours} hours available"

    class Meta:
        verbose_name_plural = "Community Time Bank"

    def deduct_hours(self, hours):
        """
        Safely deduct hours from the community timebank.
        Returns True if successful, False if insufficient hours.
        """
        if self.total_hours >= hours:
            self.total_hours -= hours
            self.save()
            return True
        return False


class TimeBankLedger(models.Model):
    TRANSACTION_TYPES = [
        ("credit", "Credit"),
        ("debit", "Debit"),
        ("community_donation", "Community Donation"),
        ("community_request", "Community Request"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    service_request = models.ForeignKey(ServiceRequest, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    hours = models.DecimalField(max_digits=5, decimal_places=2)
    balance = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_type} of {self.hours} hours for {self.user.username}"

    class Meta:
        ordering = ["-created_at"]


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to="profile_images/", blank=True)
    bio = models.TextField(blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    total_hours_earned = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_hours_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    terms_accepted = models.BooleanField(
        default=False,
        help_text="User has agreed to use the platform responsibly and not engage in malicious activities or illegal behavior.",
    )
    terms_accepted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}'s profile"

    @property
    def time_balance(self):
        return self.total_hours_earned - self.total_hours_spent

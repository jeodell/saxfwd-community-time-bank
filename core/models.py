import uuid

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        user = self.model(
            email=self.normalize_email(email),
            first_name=extra_fields.get("first_name"),
            last_name=extra_fields.get("last_name"),
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        user = self.create_user(
            email,
            password=password,
            first_name=extra_fields.get("first_name"),
            last_name=extra_fields.get("last_name"),
        )
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.save(using=self._db)
        return user


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = None
    email = models.EmailField(_("email address"), unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    bio = models.TextField(blank=True)
    image = models.ImageField(upload_to="user_images/", blank=True)
    total_hours_earned = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_hours_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    terms_accepted = models.BooleanField(
        default=False,
        help_text="User has agreed to use the platform responsibly and not engage in malicious activities or illegal behavior.",
    )
    terms_accepted_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Fields already included - first_name, last_name, is_staff, is_active, date_joined
    # Fields overwritten - username, email

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = UserManager()

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def time_balance(self):
        return self.total_hours_earned - self.total_hours_spent

    @property
    def full_name(self):
        """Get the user's full name from the User model."""
        return f"{self.first_name} {self.last_name}".strip()


class ServiceCategory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    icon = models.CharField(max_length=50, blank=True, null=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
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
        return f"{self.title} by {self.provider.first_name} {self.provider.last_name}"

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

        return queryset.order_by("-created_at")


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

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    requester = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="service_requests"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    requested_date = models.DateTimeField()
    hours_requested = models.DecimalField(
        max_digits=5, decimal_places=2, validators=[MinValueValidator(0.5)]
    )
    hours_completed = models.DecimalField(
        max_digits=5, decimal_places=2, validators=[MinValueValidator(0.5)], default=0
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
        return f"{self.service.title} request by {self.requester.first_name} {self.requester.last_name}"

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
        if not community_bank.deduct_hours(self.hours_completed):
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
            hours=self.hours_completed,
            balance=self.requester.time_balance,
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
            hours = self.hours_completed
            provider = User.objects.get_or_create(user=self.service.provider)[0]
            requester = User.objects.get_or_create(user=self.requester)[0]

            # Credit provider
            TimeBankLedger.objects.create(
                user=self.service.provider,
                service_request=self,
                transaction_type="credit",
                hours=hours,
                balance=provider.total_hours_earned + hours,
                description=f"Completed service: {self.service.title}",
            )
            provider.total_hours_earned += hours
            provider.save()

            # Debit requester
            TimeBankLedger.objects.create(
                user=self.requester,
                service_request=self,
                transaction_type="debit",
                hours=hours,
                balance=requester.total_hours_spent + hours,
                description=f"Received service: {self.service.title}",
            )
            requester.total_hours_spent += hours
            requester.save()

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

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    service_request = models.ForeignKey(ServiceRequest, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    hours = models.DecimalField(max_digits=5, decimal_places=2)
    balance = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_type} of {self.hours} hours for {self.user.first_name} {self.user.last_name}"

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        # Update user's time balance
        if self.transaction_type == "credit":
            self.user.time_balance += self.hours
        else:  # debit
            self.user.time_balance -= self.hours
        self.user.save()
        super().save(*args, **kwargs)

    @classmethod
    def get_user_transactions(
        cls, user, transaction_type=None, start_date=None, end_date=None
    ):
        """
        Get a user's transaction history with optional filtering.

        Args:
            user: The user to get transactions for
            transaction_type: Optional filter by transaction type
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering
        """
        queryset = cls.objects.filter(user=user)

        if transaction_type:
            queryset = queryset.filter(transaction_type=transaction_type)

        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)

        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)

        return queryset

    @classmethod
    def get_user_balance(cls, user):
        """Get a user's current time balance."""
        return user.time_balance

    @classmethod
    def get_user_earnings(cls, user, start_date=None, end_date=None):
        """Get a user's total earnings for a period."""
        queryset = cls.objects.filter(user=user, transaction_type="credit")

        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)

        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)

        return queryset.aggregate(total=models.Sum("hours"))["total"] or 0

    @classmethod
    def get_user_spending(cls, user, start_date=None, end_date=None):
        """Get a user's total spending for a period."""
        queryset = cls.objects.filter(user=user, transaction_type="debit")

        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)

        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)

        return queryset.aggregate(total=models.Sum("hours"))["total"] or 0

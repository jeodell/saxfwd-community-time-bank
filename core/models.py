import uuid
from datetime import datetime
from decimal import Decimal
from io import BytesIO

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from PIL import Image


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

    def user_image_path(instance, filename):
        ext = filename.split(".")[-1]
        return f"uploads/user_images/{instance.id}.{ext}"

    image = models.ImageField(upload_to=user_image_path, blank=True)
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
        """Calculate current balance from ledger entries."""
        service_credits = TimeBankLedger.objects.filter(
            user=self, transaction_type="service_credit"
        ).aggregate(total=models.Sum("hours"))["total"] or Decimal("0.00")

        request_credits = TimeBankLedger.objects.filter(
            user=self, transaction_type="request_credit"
        ).aggregate(total=models.Sum("hours"))["total"] or Decimal("0.00")

        application_credits = TimeBankLedger.objects.filter(
            user=self, transaction_type="application_credit"
        ).aggregate(total=models.Sum("hours"))["total"] or Decimal("0.00")

        service_debits = TimeBankLedger.objects.filter(
            user=self, transaction_type="service_debit"
        ).aggregate(total=models.Sum("hours"))["total"] or Decimal("0.00")

        request_debits = TimeBankLedger.objects.filter(
            user=self, transaction_type="request_debit"
        ).aggregate(total=models.Sum("hours"))["total"] or Decimal("0.00")

        community_donations = TimeBankLedger.objects.filter(
            user=self, transaction_type="community_donation"
        ).aggregate(total=models.Sum("hours"))["total"] or Decimal("0.00")

        return (service_credits + request_credits + application_credits) - (
            service_debits + request_debits + community_donations
        )

    @property
    def total_hours_earned(self):
        """Calculate total hours earned from ledger entries."""
        service_credits = TimeBankLedger.objects.filter(
            user=self, transaction_type="service_credit"
        ).aggregate(total=models.Sum("hours"))["total"] or Decimal("0.00")

        request_credits = TimeBankLedger.objects.filter(
            user=self, transaction_type="request_credit"
        ).aggregate(total=models.Sum("hours"))["total"] or Decimal("0.00")

        application_credits = TimeBankLedger.objects.filter(
            user=self, transaction_type="application_credit"
        ).aggregate(total=models.Sum("hours"))["total"] or Decimal("0.00")

        return service_credits + request_credits + application_credits

    @property
    def total_hours_spent(self):
        """Calculate total hours spent from ledger entries."""
        service_debits = TimeBankLedger.objects.filter(
            user=self, transaction_type="service_debit"
        ).aggregate(total=models.Sum("hours"))["total"] or Decimal("0.00")

        request_debits = TimeBankLedger.objects.filter(
            user=self, transaction_type="request_debit"
        ).aggregate(total=models.Sum("hours"))["total"] or Decimal("0.00")

        community_donations = TimeBankLedger.objects.filter(
            user=self, transaction_type="community_donation"
        ).aggregate(total=models.Sum("hours"))["total"] or Decimal("0.00")

        community_requests = TimeBankLedger.objects.filter(
            user=self, transaction_type="community_request"
        ).aggregate(total=models.Sum("hours"))["total"] or Decimal("0.00")

        return (
            service_debits + request_debits + community_requests + community_donations
        )

    @property
    def full_name(self):
        """Get the user's full name from the User model."""
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def is_fully_approved(self):
        """Check if user has both referral approval and orientation completed."""
        return self.is_referral_approved and self.is_orientation_completed

    @property
    def is_referral_approved(self):
        """Check if user has referral approval through their application."""
        try:
            return self.application.is_referral_approved
        except Application.DoesNotExist:
            return False

    @property
    def referral_approved_by(self):
        """Get the user who approved the referral from the application."""
        try:
            return self.application.referral_approved_by
        except Application.DoesNotExist:
            return None

    @property
    def referral_approved_at(self):
        """Get the referral approval timestamp from the application."""
        try:
            return self.application.referral_approved_at
        except Application.DoesNotExist:
            return None

    @property
    def is_orientation_completed(self):
        """Check if user has completed orientation through their application."""
        try:
            return self.application.is_orientation_completed
        except Application.DoesNotExist:
            return False

    @property
    def orientation_at(self):
        """Get the orientation completion timestamp from the application."""
        try:
            return self.application.orientation_at
        except Application.DoesNotExist:
            return None

    @property
    def can_login(self):
        """Check if user can log in (must be active and fully approved)."""
        return self.is_active and self.is_fully_approved

    def process_image(self):
        """Process and resize the user's image. Call this method when the image is updated."""
        if not self.image:
            return

        # Delete the old image file if it has changed
        if self.pk:
            try:
                user = User.objects.get(pk=self.pk)
                if user.image and user.image != self.image:
                    # Use storage backend to delete the file (works with both local and S3)
                    user.image.delete(save=False)
            except User.DoesNotExist:
                pass

        # Resize and crop image to 200x200
        img = Image.open(self.image)
        if img.mode in ("RGBA", "LA"):
            background = Image.new("RGB", img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[-1])
            img = background

        # Crop image to square
        width, height = img.size
        size = min(width, height)
        left = (width - size) // 2
        top = (height - size) // 2
        right = left + size
        bottom = top + size
        img = img.crop((left, top, right, bottom))

        # Resize image to thumbnail size (200x200)
        img = img.resize((200, 200), Image.Resampling.LANCZOS)

        # Save the resized image
        buffer = BytesIO()
        img.save(buffer, format="JPEG", quality=85)
        buffer.seek(0)

        # Generate new filename
        ext = self.image.name.split(".")[-1]
        filename = f"{self.id}.{ext}"

        # Save the resized image
        self.image.save(filename, ContentFile(buffer.read()), save=False)

    def save(self, *args, **kwargs):
        # Check if this is just a last_login update and skip image processing if so
        if self.pk and len(args) == 0 and kwargs.get("update_fields") == ["last_login"]:
            super().save(*args, **kwargs)
            return

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Delete the image file when the user is deleted
        if self.image:
            # Use the storage backend to delete the file (works with both local and S3)
            self.image.delete(save=False)
        super().delete(*args, **kwargs)


class ServiceCategory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    color = models.CharField(max_length=7, default="#000000")
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
    availability = models.TextField(blank=True, null=True)
    experience = models.TextField(blank=True, null=True)
    provider = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="services_provided"
    )
    category = models.ForeignKey(ServiceCategory, on_delete=models.SET_NULL, null=True)
    max_hours = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        validators=[MinValueValidator(0.25)],
        help_text="Maximum number of hours per service request",
        null=True,
        blank=True,
    )
    max_hours_per_month = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        validators=[MinValueValidator(0.25)],
        help_text="Maximum number of hours per month",
        null=True,
        blank=True,
    )
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} by {self.provider.first_name} {self.provider.last_name}"

    def can_be_edited_by(self, user):
        """Check if the service can be edited by the provider user."""
        return user == self.provider

    def get_monthly_hours_used(self):
        """Calculate the total hours used for this service in the current month."""
        # Get the first day of the current month
        now = timezone.now()
        first_day = datetime(now.year, now.month, 1, tzinfo=now.tzinfo)

        # Get all completed service requests for this service in the current month
        completed_requests = self.service_transactions.filter(
            status="completed", completed_at__gte=first_day, completed_at__lte=now
        )

        # Sum up the hours completed
        total_hours = sum(
            request.hours_completed or request.hours_requested
            for request in completed_requests
        )

        return Decimal(str(total_hours))

    def get_monthly_hours_percentage(self):
        """Calculate the percentage of monthly hours used."""
        if not self.max_hours_per_month:
            return 0

        monthly_hours = self.get_monthly_hours_used()
        percentage = (monthly_hours / self.max_hours_per_month) * 100
        return min(percentage, 100)  # Cap at 100%

    @classmethod
    def get_active_services(cls, category=None, search=None):
        """
        Get active services with optional filtering.

        Args:
            category: Category name to filter by
            search: Search term to filter by title or description
        """
        queryset = cls.objects.filter(is_active=True, is_deleted=False)

        if category:
            queryset = queryset.filter(category__name=category)

        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )

        return queryset.order_by("-created_at")


class ServiceTransaction(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("completed", "Completed"),
        ("canceled", "Canceled"),
        ("rejected", "Rejected"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service = models.ForeignKey(
        Service, on_delete=models.CASCADE, related_name="service_transactions"
    )
    requester = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="service_requests"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    requested_date = models.DateTimeField()
    hours_requested = models.DecimalField(
        max_digits=4, decimal_places=2, validators=[MinValueValidator(0.25)]
    )
    hours_completed = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    description = models.TextField()
    rejection_reason = models.TextField(
        blank=True, help_text="Reason for rejecting this service request"
    )
    cancellation_reason = models.TextField(
        blank=True, help_text="Reason for cancelling this service request"
    )
    provider_completed = models.BooleanField(default=False)
    requester_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def clean(self):
        """Validate that hours_requested doesn't exceed service's max_hours."""
        if (
            hasattr(self, "service")
            and self.service
            and self.service.max_hours
            and self.hours_requested > self.service.max_hours
        ):
            raise ValidationError(
                {
                    "hours_requested": f"Cannot request more than {self.service.max_hours} hours for this service."
                }
            )
        super().clean()

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.service.title} transaction by {self.requester.first_name} {self.requester.last_name}"

    class Meta:
        verbose_name_plural = "Service Transactions"

    @property
    def can_be_approved(self):
        """Check if this service request can be approved."""
        return self.status == "pending"

    @property
    def can_be_rejected(self):
        """Check if this service request can be rejected."""
        return self.status == "pending"

    def accept_request(self):
        """
        Accept this service request.
        """
        if self.status != "pending":
            raise ValueError("This request cannot be accepted")

        self.status = "accepted"
        self.save()

    def reject_request(self, reason=""):
        """
        Reject this service request.

        Args:
            reason: Optional reason for rejecting the request
        """
        if self.status != "pending":
            raise ValueError("This request cannot be rejected")

        self.status = "rejected"
        self.rejection_reason = reason
        self.save()

    def cancel_request(self, reason=None):
        """
        Cancel this service request.
        """
        if self.status != "pending":
            raise ValueError("This request cannot be canceled")
        self.status = "canceled"
        if reason:
            self.cancellation_reason = reason
        self.save()

    def complete_request(self, user, hours_completed=None):
        """
        Mark this request as complete by either the provider or requester.
        Returns True if both parties have completed, False otherwise.
        """
        if self.status != "accepted":
            raise ValueError("This request cannot be completed")

        if user == self.service.provider:
            self.provider_completed = True
            if hours_completed is not None:
                self.hours_completed = hours_completed
        elif user == self.requester:
            self.requester_completed = True
        else:
            raise ValueError("Only the provider or requester can complete this request")

        if self.provider_completed and self.requester_completed:
            self.status = "completed"
            self.completed_at = timezone.now()

            # Use hours_completed if set, otherwise use hours_requested
            hours = (
                self.hours_completed
                if self.hours_completed > 0
                else self.hours_requested
            )
            provider = self.service.provider
            requester = self.requester

            # Create ledger entries for the transaction
            TimeBankLedger.objects.create(
                user=provider,
                service_transaction=self,
                transaction_type="service_credit",
                hours=hours,
                description=self.service.title,
            )

            TimeBankLedger.objects.create(
                user=requester,
                service_transaction=self,
                transaction_type="service_debit",
                hours=hours,
                description=self.service.title,
            )

        self.save()
        return self.provider_completed and self.requester_completed

    def can_request_community_hours(self):
        """Check if this service request can be converted to a community request."""
        return self.status == "pending"

    def request_community_hours(self, reason):
        """Convert this service request to a community request."""
        if not self.can_request_community_hours():
            raise ValueError("This request cannot be converted to a community request")

        # Create a new CommunityTransaction instance
        community_request = CommunityTransaction.objects.create(
            servicetransaction_ptr=self, reason=reason, community_status="pending"
        )
        return community_request

    def approve_community_request(self, reviewer, notes=""):
        """Approve this service request as a community request."""
        if not isinstance(self, CommunityTransaction):
            raise ValueError("This is not a community request")
        return self.approve(reviewer, notes)

    def reject_community_request(self, reviewer, notes=""):
        """Reject this service request as a community request."""
        if not isinstance(self, CommunityTransaction):
            raise ValueError("This is not a community request")
        return self.reject(reviewer, notes)

    @property
    def hours_completed_calculated(self):
        """
        Calculate actual hours completed from ledger entries.
        Returns the hours from the service_credit ledger entry if it exists,
        otherwise returns hours_requested.
        """
        try:
            # Get the service_credit ledger entry for this transaction
            ledger_entry = TimeBankLedger.objects.get(
                service_transaction=self, transaction_type="service_credit"
            )
            return ledger_entry.hours
        except TimeBankLedger.DoesNotExist:
            # If no ledger entry exists, return the requested hours
            return self.hours_requested


class Request(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField()
    preferred_date = models.DateField(null=True, blank=True)
    requester = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="requests_made"
    )
    category = models.ForeignKey(ServiceCategory, on_delete=models.SET_NULL, null=True)
    estimated_hours = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        validators=[MinValueValidator(0.25)],
        help_text="Estimated number of hours to complete the service",
        null=True,
        blank=True,
    )
    num_users_needed = models.IntegerField(default=1)
    priority = models.CharField(
        max_length=20,
        choices=[("low", "Low"), ("medium", "Medium"), ("high", "High")],
        default="medium",
    )
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} by {self.requester.first_name} {self.requester.last_name}"

    class Meta:
        verbose_name_plural = "Requests"

    def can_be_edited_by(self, user):
        """Check if the request can be edited by the requester."""
        return user == self.requester

    @property
    def accepted_offers_count(self):
        """Count the number of accepted offers for this request."""
        return RequestTransaction.objects.filter(
            request=self, status="accepted"
        ).count()

    @property
    def is_fully_staffed(self):
        """Check if the request has enough accepted offers to meet the required number of users."""
        return self.accepted_offers_count >= self.num_users_needed

    @classmethod
    def get_active_requests(cls, category=None, search=None):
        """
        Get active requests with optional filtering.

        Args:
            category: Category name to filter by
            search: Search term to filter by title or description
        """
        queryset = cls.objects.filter(is_active=True, is_deleted=False)

        if category:
            queryset = queryset.filter(category__name=category)

        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )

        return queryset.order_by("-created_at")


class RequestTransaction(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("completed", "Completed"),
        ("canceled", "Canceled"),
        ("rejected", "Rejected"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    request = models.ForeignKey(
        Request, on_delete=models.CASCADE, related_name="offers"
    )
    provider = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="request_offers"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    proposed_hours = models.DecimalField(
        max_digits=4, decimal_places=2, validators=[MinValueValidator(0.25)]
    )
    hours_completed = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    message = models.TextField(help_text="Why you'd like to help with this request")
    rejection_reason = models.TextField(
        blank=True, help_text="Reason for rejecting this offer"
    )
    cancellation_reason = models.TextField(
        blank=True, help_text="Reason for cancelling this offer"
    )
    provider_completed = models.BooleanField(default=False)
    requester_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Offer for {self.request.title} by {self.provider.first_name} {self.provider.last_name}"

    class Meta:
        verbose_name_plural = "Request Transactions"

    @property
    def can_be_approved(self):
        """Check if this offer can be approved."""
        return self.status == "pending"

    @property
    def can_be_rejected(self):
        """Check if this offer can be rejected."""
        return self.status == "pending"

    def accept_offer(self):
        """
        Accept this offer.
        """
        if self.status != "pending":
            raise ValueError("This offer cannot be accepted")

        self.status = "accepted"
        self.save()

    def reject_offer(self, reason=""):
        """
        Reject this offer.

        Args:
            reason: Optional reason for rejecting the offer
        """
        if self.status != "pending":
            raise ValueError("This offer cannot be rejected")

        self.status = "rejected"
        self.rejection_reason = reason
        self.save()

    def cancel_offer(self, reason=None):
        """
        Cancel this offer.
        """
        if self.status != "pending":
            raise ValueError("This offer cannot be canceled")
        self.status = "canceled"
        if reason:
            self.cancellation_reason = reason
        self.save()

    def complete_offer(self, user, hours_completed=None):
        """
        Mark this offer as complete by either the provider or requester.
        Returns True if both parties have completed, False otherwise.
        """
        if self.status != "accepted":
            raise ValueError("This offer cannot be completed")

        if user == self.provider:
            self.provider_completed = True
            if hours_completed is not None:
                self.hours_completed = hours_completed
        elif user == self.request.requester:
            self.requester_completed = True
        else:
            raise ValueError("Only the provider or requester can complete this offer")

        if self.provider_completed and self.requester_completed:
            self.status = "completed"
            self.completed_at = timezone.now()

            # Use hours_completed if set, otherwise use proposed_hours
            hours = (
                self.hours_completed
                if self.hours_completed > 0
                else self.proposed_hours
            )
            provider = self.provider
            requester = self.request.requester

            # Create ledger entries for the transaction
            TimeBankLedger.objects.create(
                user=provider,
                request_transaction=self,
                transaction_type="request_credit",
                hours=hours,
                description=self.request.title,
            )

            TimeBankLedger.objects.create(
                user=requester,
                request_transaction=self,
                transaction_type="request_debit",
                hours=hours,
                description=self.request.title,
            )

        self.save()
        return self.provider_completed and self.requester_completed

    @property
    def hours_completed_calculated(self):
        """
        Calculate actual hours completed from ledger entries.
        Returns the hours from the request_credit ledger entry if it exists,
        otherwise returns proposed_hours.
        """
        try:
            # Get the request_credit ledger entry for this transaction
            ledger_entry = TimeBankLedger.objects.get(
                request_transaction=self, transaction_type="request_credit"
            )
            return ledger_entry.hours
        except TimeBankLedger.DoesNotExist:
            # If no ledger entry exists, return the proposed hours
            return self.proposed_hours


class CommunityTransaction(ServiceTransaction):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    community_status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending"
    )
    reason = models.TextField(help_text="Please explain why you need community hours")
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_community_requests",
    )
    review_notes = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Community request for {self.service.title} by {self.requester.first_name} {self.requester.last_name}"

    def approve(self, reviewer, notes=""):
        """
        Approve this community request and deduct hours from the community timebank.
        """
        if self.community_status != "pending":
            raise ValueError("This request is not pending approval")

        # Get the community timebank
        community_bank = CommunityHours.get_instance()

        # Check if we have enough hours
        hours_to_deduct = self.hours_completed
        if hours_to_deduct == 0:
            hours_to_deduct = self.hours_requested

        # Check if we have enough community hours available
        if community_bank.total_hours < hours_to_deduct:
            raise ValueError("Insufficient community hours available")

        # Update the request
        self.community_status = "approved"
        self.reviewed_by = reviewer
        self.review_notes = notes
        self.reviewed_at = timezone.now()
        self.save()

        # Create a ledger entry for the community hours usage
        TimeBankLedger.objects.create(
            user=self.requester,
            service_transaction=self,
            transaction_type="community_request",
            hours=hours_to_deduct,
            description=self.service.title,
        )

    def reject(self, reviewer, notes=""):
        """
        Reject this community request.
        """
        if self.community_status != "pending":
            raise ValueError("This request is not pending approval")

        self.community_status = "rejected"
        self.reviewed_by = reviewer
        self.review_notes = notes
        self.reviewed_at = timezone.now()
        self.save()

    @property
    def can_be_approved(self):
        """Check if this community request can be approved."""
        return self.community_status == "pending" and self.status == "pending"

    @property
    def can_be_rejected(self):
        """Check if this community request can be rejected."""
        return self.community_status == "pending" and self.status == "pending"

    def accept_request(self):
        """
        Accept this community request.
        """
        if self.community_status != "approved":
            raise ValueError("Community request must be approved before accepting")
        if self.status != "pending":
            raise ValueError("This request cannot be accepted")
        super().accept_request()


class CommunityHours(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Community Time Bank: {self.total_hours} hours available"

    class Meta:
        verbose_name_plural = "Community Time Bank"

    @property
    def total_hours(self):
        """
        Calculate total community hours from ledger entries.
        Community hours = donations - requests
        """
        donations = TimeBankLedger.objects.filter(
            transaction_type="community_donation"
        ).aggregate(total=models.Sum("hours"))["total"] or Decimal("0.00")

        requests = TimeBankLedger.objects.filter(
            transaction_type="community_request"
        ).aggregate(total=models.Sum("hours"))["total"] or Decimal("0.00")

        return donations - requests

    @classmethod
    def get_instance(cls):
        """
        Get or create the single CommunityHours instance.
        This ensures we always have exactly one instance.
        """
        instance, _ = cls.objects.get_or_create()
        return instance


class TimeBankLedger(models.Model):
    TRANSACTION_TYPES = [
        ("service_credit", "Service Credit"),
        ("service_debit", "Service Debit"),
        ("community_donation", "Community Donation"),
        ("community_request", "Community Request"),
        ("request_credit", "Request Credit"),
        ("request_debit", "Request Debit"),
        ("application_credit", "Application Approval Credit"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    service_transaction = models.ForeignKey(
        ServiceTransaction, on_delete=models.CASCADE, null=True, blank=True
    )
    request_transaction = models.ForeignKey(
        RequestTransaction, on_delete=models.CASCADE, null=True, blank=True
    )
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    hours = models.DecimalField(
        max_digits=4, decimal_places=2, validators=[MinValueValidator(0.25)]
    )
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_type} of {self.hours} hours for {self.user.first_name} {self.user.last_name}"

    class Meta:
        ordering = ["-created_at"]


class MeetingNotes(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    meeting_date = models.DateField()
    pdf_file = models.FileField(upload_to="uploads/meeting_notes/")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.meeting_date}"

    class Meta:
        ordering = ["-meeting_date", "-created_at"]
        verbose_name_plural = "Meeting Notes"

    def clean(self):
        if self.pdf_file:
            # Validate file extension
            if not self.pdf_file.name.lower().endswith(".pdf"):
                raise ValidationError("Only PDF files are allowed.")

            # Validate file size (max 10MB)
            if self.pdf_file.size > 10 * 1024 * 1024:  # 10MB
                raise ValidationError("File size must be under 10MB.")

    def delete(self, *args, **kwargs):
        # Delete the PDF file when the meeting notes are deleted
        if self.pdf_file:
            # Use the storage backend to delete the file (works with both local and S3)
            self.pdf_file.delete(save=False)
        super().delete(*args, **kwargs)


class Application(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="application"
    )

    # Application fields
    referral_member = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="referrals_made",
    )
    writeup = models.TextField()

    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    # Referral approval tracking
    is_referral_approved = models.BooleanField(default=False)
    referral_approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_applications",
    )
    referral_approved_at = models.DateTimeField(null=True, blank=True)

    # Orientation tracking
    is_orientation_completed = models.BooleanField(default=False)
    orientation_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Application from {self.user.full_name}"

    class Meta:
        ordering = ["-created_at"]

    def approve(self, reviewer, notes=""):
        """Approve the application and mark the user as referral approved."""
        self.is_referral_approved = True
        self.referral_approved_by = reviewer
        self.referral_approved_at = timezone.now()
        self.save()

        # Add 5 hours of credits for application approval
        TimeBankLedger.objects.create(
            user=self.user,
            transaction_type="application_credit",
            hours=Decimal("5.00"),
            description="Welcome bonus for approved application",
        )

    def mark_orientation_completed(self):
        """Mark the user as having completed orientation."""
        self.is_orientation_completed = True
        self.orientation_at = timezone.now()
        if self.is_referral_approved and self.status == "pending":
            self.status = "approved"
        self.save()

    def reject(self, reviewer, notes=""):
        """Reject the application."""
        self.status = "rejected"
        self.save()

    @property
    def can_be_approved(self):
        """Check if the application can be approved."""
        return self.status == "pending"

    @property
    def can_be_rejected(self):
        """Check if the application can be rejected."""
        return self.status == "pending"

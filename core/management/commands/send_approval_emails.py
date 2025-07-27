from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from core.views.base import send_approval_email

User = get_user_model()


class Command(BaseCommand):
    help = "Send approval emails to fully approved users who haven't set their password yet"

    def add_arguments(self, parser):
        parser.add_argument(
            "--user-id",
            type=str,
            help="Send approval email to a specific user by ID",
        )
        parser.add_argument(
            "--email",
            type=str,
            help="Send approval email to a specific user by email",
        )

    def handle(self, *args, **options):
        if options["user_id"]:
            try:
                user = User.objects.get(id=options["user_id"])
                if user.is_fully_approved and not user.has_usable_password():
                    if send_approval_email(user):
                        self.stdout.write(
                            self.style.SUCCESS(f"Approval email sent to {user.email}")
                        )
                    else:
                        self.stdout.write(
                            self.style.ERROR(
                                f"Failed to send approval email to {user.email}"
                            )
                        )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f"User {user.email} is not eligible for approval email"
                        )
                    )
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"User with ID {options['user_id']} not found")
                )

        elif options["email"]:
            try:
                user = User.objects.get(email=options["email"])
                if user.is_fully_approved and not user.has_usable_password():
                    if send_approval_email(user):
                        self.stdout.write(
                            self.style.SUCCESS(f"Approval email sent to {user.email}")
                        )
                    else:
                        self.stdout.write(
                            self.style.ERROR(
                                f"Failed to send approval email to {user.email}"
                            )
                        )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f"User {user.email} is not eligible for approval email"
                        )
                    )
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"User with email {options['email']} not found")
                )

        else:
            # Send to all eligible users
            eligible_users = User.objects.filter(
                application__is_referral_approved=True,
                application__is_orientation_completed=True,
                is_active=False,
            )

            sent_count = 0
            for user in eligible_users:
                if not user.has_usable_password():
                    if send_approval_email(user):
                        sent_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(f"Approval email sent to {user.email}")
                        )
                    else:
                        self.stdout.write(
                            self.style.ERROR(
                                f"Failed to send approval email to {user.email}"
                            )
                        )

            self.stdout.write(
                self.style.SUCCESS(f"Successfully sent {sent_count} approval emails")
            )

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand
from django.core.validators import validate_email
from django.utils import timezone

User = get_user_model()


class Command(BaseCommand):
    help = "Create a Django admin user"

    def add_arguments(self, parser):
        parser.add_argument(
            "--email",
            type=str,
            help="Email address for the admin user",
        )
        parser.add_argument(
            "--password",
            type=str,
            help="Password for the admin user",
        )
        parser.add_argument(
            "--first-name",
            type=str,
            help="First name for the admin user",
        )
        parser.add_argument(
            "--last-name",
            type=str,
            help="Last name for the admin user",
        )
        parser.add_argument(
            "--phone",
            type=str,
            help="Phone number for the admin user",
        )
        parser.add_argument(
            "--address",
            type=str,
            help="Address for the admin user",
        )
        parser.add_argument(
            "--bio",
            type=str,
            help="Bio for the admin user",
        )
        parser.add_argument(
            "--non-interactive",
            action="store_true",
            help="Run in non-interactive mode (requires all arguments)",
        )

    def handle(self, *args, **options):
        if options["non_interactive"]:
            # Non-interactive mode - require all arguments
            required_fields = ["email", "password", "first_name", "last_name"]
            missing_fields = [
                field for field in required_fields if not options.get(field)
            ]

            if missing_fields:
                self.stdout.write(
                    self.style.ERROR(
                        f"Non-interactive mode requires all arguments. Missing: {', '.join(missing_fields)}"
                    )
                )
                return

        # Get user input
        email = options.get("email")
        if not email:
            email = input("Email address: ").strip()

        # Validate email
        try:
            validate_email(email)
        except ValidationError:
            self.stdout.write(self.style.ERROR("Invalid email address"))
            return

        # Check if user already exists
        if User.objects.filter(email=email).exists():
            self.stdout.write(
                self.style.WARNING(f"User with email {email} already exists")
            )
            return

        password = options.get("password")
        if not password:
            password = input("Password: ").strip()
            if not password:
                self.stdout.write(self.style.ERROR("Password cannot be empty"))
                return

        first_name = options.get("first_name")
        if not first_name:
            first_name = input("First name: ").strip()
            if not first_name:
                self.stdout.write(self.style.ERROR("First name cannot be empty"))
                return

        last_name = options.get("last_name")
        if not last_name:
            last_name = input("Last name: ").strip()
            if not last_name:
                self.stdout.write(self.style.ERROR("Last name cannot be empty"))
                return

        phone = options.get("phone")
        if not phone:
            phone = input("Phone number (optional): ").strip()

        address = options.get("address")
        if not address:
            address = input("Address (optional): ").strip()

        bio = options.get("bio")
        if not bio:
            bio = input("Bio (optional): ").strip()

        # Create the admin user
        try:
            user = User.objects.create_user(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                phone_number=phone or "",
                address=address or "",
                bio=bio or "",
                is_staff=True,
                is_superuser=True,
                is_active=True,
                terms_accepted=True,
                terms_accepted_at=timezone.now(),
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ Admin user created successfully!\n"
                    f"📧 Email: {user.email}\n"
                    f"👤 Name: {user.full_name}\n"
                    f"🔑 Password: {'*' * len(password)}\n"
                    f"🔧 Staff: {user.is_staff}\n"
                    f"👑 Superuser: {user.is_superuser}"
                )
            )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error creating admin user: {str(e)}"))

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from core.models import Service, ServiceCategory

User = get_user_model()

CATEGORIES = [
    {"name": "Arts and Crafts", "is_featured": True},
    {"name": "Education", "is_featured": False},
    {"name": "Elder Care", "is_featured": False},
    {"name": "Entertainment", "is_featured": False},
    {"name": "Financial", "is_featured": True},
    {"name": "Fitness", "is_featured": False},
    {"name": "Food", "is_featured": True},
    {"name": "General Labor", "is_featured": True},
    {"name": "Healthcare", "is_featured": False},
    {"name": "Home", "is_featured": True},
    {"name": "Landscaping", "is_featured": True},
    {"name": "Legal", "is_featured": False},
    {"name": "Other", "is_featured": False},
    {"name": "Pet", "is_featured": False},
    {"name": "Repair", "is_featured": False},
    {"name": "Tech", "is_featured": True},
    {"name": "Transportation", "is_featured": False},
    {"name": "Wellness", "is_featured": False},
]

DESCRIPTION = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Aenean a."

USERS = [
    {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "password": "password",
    },
    {
        "first_name": "Jane",
        "last_name": "Doe",
        "email": "jane.doe@example.com",
        "password": "password",
    },
]

SERVICES = [
    {
        "title": "Lawn Care",
        "description": "Mow the lawn, trim the hedges, and clean up the yard.",
        "category": "Landscaping",
        "provider_email": "john.doe@example.com",
    },
    {
        "title": "Housekeeping",
        "description": "Clean the house, dust, vacuum, and mop the floors.",
        "category": "Home",
        "provider_email": "jane.doe@example.com",
    },
    {
        "title": "Pet Care",
        "description": "Feed, walk, and play with the pet.",
        "category": "Pet",
        "provider_email": "john.doe@example.com",
    },
]


class Command(BaseCommand):
    help = "Seed the database with default service categories"

    def handle(self, *args, **kwargs):
        # Create categories
        for category in CATEGORIES:
            obj, created = ServiceCategory.objects.get_or_create(
                name=category["name"],
                defaults={
                    "description": DESCRIPTION,
                    "is_featured": category["is_featured"],
                },
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f"Created category: {category['name']}")
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f"Category already exists: {category['name']}")
                )

        # Create users
        for user_data in USERS:
            user, created = User.objects.get_or_create(
                email=user_data["email"],
                defaults={
                    "first_name": user_data["first_name"],
                    "last_name": user_data["last_name"],
                    "is_active": True,
                    "is_staff": True,
                    "is_superuser": True,
                },
            )
            if created:
                user.set_password(user_data["password"])
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Created user: {user_data['first_name']} {user_data['last_name']}"
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"User already exists: {user_data['first_name']} {user_data['last_name']}"
                    )
                )

        # Create services
        for service_data in SERVICES:
            try:
                category = ServiceCategory.objects.get(name=service_data["category"])
                provider = User.objects.get(email=service_data["provider_email"])

                service, created = Service.objects.get_or_create(
                    title=service_data["title"],
                    provider=provider,
                    defaults={
                        "description": service_data["description"],
                        "category": category,
                        "is_active": True,
                    },
                )

                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f"Created service: {service_data['title']}")
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Service already exists: {service_data['title']}"
                        )
                    )
            except ServiceCategory.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"Category not found: {service_data['category']}")
                )
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(
                        f"Provider not found: {service_data['provider_email']}"
                    )
                )

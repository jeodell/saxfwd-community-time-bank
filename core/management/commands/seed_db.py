from django.core.management.base import BaseCommand

from core.models import ServiceCategory

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
    {"name": "Home", "is_featured": False},
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


class Command(BaseCommand):
    help = "Seed the database with default service categories"

    def handle(self, *args, **kwargs):
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

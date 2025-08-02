import random
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import (
    Application,
    CommunityHours,
    CommunityTransaction,
    Request,
    RequestTransaction,
    Service,
    ServiceCategory,
    ServiceTransaction,
    TimeBankLedger,
    User,
)

User = get_user_model()

CATEGORIES = [
    {"name": "Arts and Crafts", "is_featured": True, "color": "#FF6B6B"},
    {"name": "Beauty", "is_featured": False, "color": "#FF8E8E"},
    {"name": "Caregiving", "is_featured": False, "color": "#FFB3B3"},
    {"name": "Conversation and Counseling", "is_featured": False, "color": "#FFB3B3"},
    {"name": "Education", "is_featured": False, "color": "#4ECDC4"},
    {"name": "Entertainment", "is_featured": False, "color": "#45B7D1"},
    {"name": "Financial", "is_featured": True, "color": "#96CEB4"},
    {"name": "Fitness", "is_featured": False, "color": "#FFEAA7"},
    {"name": "Food", "is_featured": True, "color": "#DDA0DD"},
    {"name": "General Labor", "is_featured": True, "color": "#FDCB6E"},
    {"name": "Healthcare", "is_featured": False, "color": "#74B9FF"},
    {"name": "Home", "is_featured": True, "color": "#A29BFE"},
    {"name": "Landscaping", "is_featured": True, "color": "#00B894"},
    {"name": "Legal", "is_featured": False, "color": "#6C5CE7"},
    {"name": "Other", "is_featured": False, "color": "#636E72"},
    {"name": "Pet", "is_featured": False, "color": "#FD79A8"},
    {"name": "Repair", "is_featured": False, "color": "#FAB1A0"},
    {"name": "Tech", "is_featured": True, "color": "#00CEC9"},
    {"name": "Transportation", "is_featured": False, "color": "#81ECEC"},
    {"name": "Wellness", "is_featured": False, "color": "#55A3FF"},
]

USERS = [
    {
        "first_name": "Jason",
        "last_name": "O'Dell",
        "email": "jason.odell@example.com",
        "password": "password",
        "phone_number": "555-5555",
        "address": "123 Main St, Saxapahaw, NC 27340",
        "bio": "I'm the admin of the community time bank. I'm here to help you get started and answer any questions you have.",
        "is_staff": False,
        "is_superuser": False,
    },
    {
        "first_name": "Gary",
        "last_name": "O'Dell",
        "email": "gary.odell@example.com",
        "password": "password",
        "phone_number": "555-5555",
        "address": "123 Main St, Saxapahaw, NC 27340",
        "bio": "Local artist and yoga instructor. I offer painting classes and wellness sessions.",
        "is_staff": False,
        "is_superuser": False,
    },
    {
        "first_name": "Jerry",
        "last_name": "O'Dell",
        "email": "jerry.odell@example.com",
        "password": "password",
        "phone_number": "555-0103",
        "address": "789 Pine Rd, Saxapahaw, NC 27340",
        "bio": "Handyman and carpenter. I can fix just about anything around the house.",
        "is_staff": False,
        "is_superuser": False,
    },
    {
        "first_name": "Larry",
        "last_name": "O'Dell",
        "email": "larry.odell@example.com",
        "password": "password",
        "phone_number": "555-0104",
        "address": "321 Elm St, Saxapahaw, NC 27340",
        "bio": "Certified financial advisor and tax preparer. Happy to help with budgeting and tax questions.",
        "is_staff": False,
        "is_superuser": False,
    },
]

SERVICES = [
    {
        "title": "House Cleaning Services",
        "description": "Thorough house cleaning including dusting, vacuuming, mopping, and bathroom cleaning.",
        "category": "Home",
        "provider_email": "gary.odell@example.com",
        "max_hours": Decimal("2.00"),
        "max_hours_per_month": Decimal("8.00"),
        "availability": "Tuesdays and Thursdays",
        "experience": "I've been cleaning houses for 10 years and have a lot of experience with different cleaning products and techniques.",
    },
    {
        "title": "Home Repairs and Maintenance",
        "description": "Basic home repairs, plumbing fixes, electrical work, and general maintenance tasks.",
        "category": "General Labor",
        "provider_email": "jerry.odell@example.com",
        "max_hours": Decimal("2.00"),
        "max_hours_per_month": Decimal("10.00"),
        "availability": "Weekends",
        "experience": "I've been a handyman for 10 years and have a lot of experience with different tools and techniques.",
    },
    {
        "title": "Financial Planning and Tax Help",
        "description": "Personal financial planning, budgeting advice, and basic tax preparation assistance.",
        "category": "Financial",
        "provider_email": "larry.odell@example.com",
        "max_hours": Decimal("2.00"),
        "max_hours_per_month": Decimal("5.00"),
        "availability": "Weekday evenings",
        "experience": "I've been a financial advisor for 10 years and have a lot of experience with different financial products and techniques.",
    },
    {
        "title": "Yoga and Wellness Sessions",
        "description": "Private or small group yoga sessions, meditation guidance, and wellness coaching.",
        "category": "Wellness",
        "provider_email": "gary.odell@example.com",
        "max_hours": Decimal("1.50"),
        "max_hours_per_month": Decimal("4.00"),
        "availability": "Mornings and evenings",
        "experience": "I've been a yoga instructor for 10 years and have a lot of experience with different yoga techniques and styles.",
    },
    {
        "title": "Art Classes and Creative Workshops",
        "description": "Painting, drawing, and creative art classes for all skill levels. Materials provided.",
        "category": "Arts and Crafts",
        "provider_email": "jerry.odell@example.com",
        "max_hours": Decimal("2.00"),
        "max_hours_per_month": Decimal("5.00"),
        "availability": "Weekend afternoons",
        "experience": "I've been an artist for 10 years and have a lot of experience with different art techniques and styles.",
    },
]

REQUESTS = [
    {
        "title": "Help Moving Furniture",
        "description": "Need help moving a couch and dining table from the garage to the living room. The furniture is heavy and I can't do it alone.",
        "category": "General Labor",
        "requester_email": "larry.odell@example.com",
        "estimated_hours": Decimal("1.00"),
        "num_users_needed": 2,
        "priority": "medium",
        "preferred_date": timezone.now().date() + timedelta(days=7),
    },
    {
        "title": "Garden Design Consultation",
        "description": "Looking for advice on redesigning my backyard garden. I want to create a more sustainable and beautiful space.",
        "category": "Landscaping",
        "requester_email": "gary.odell@example.com",
        "estimated_hours": Decimal("1.00"),
        "num_users_needed": 1,
        "priority": "low",
        "preferred_date": timezone.now().date() + timedelta(days=14),
    },
    {
        "title": "Computer Setup for Senior",
        "description": "My mother needs help setting up her new laptop and learning basic computer skills. She's a complete beginner.",
        "category": "Tech",
        "requester_email": "jerry.odell@example.com",
        "estimated_hours": Decimal("1.50"),
        "num_users_needed": 1,
        "priority": "medium",
        "preferred_date": timezone.now().date() + timedelta(days=3),
    },
    {
        "title": "Budget Planning Session",
        "description": "I need help creating a monthly budget and getting my finances organized. I'm not sure where to start.",
        "category": "Financial",
        "requester_email": "larry.odell@example.com",
        "estimated_hours": Decimal("1.50"),
        "num_users_needed": 1,
        "priority": "high",
        "preferred_date": timezone.now().date() + timedelta(days=2),
    },
]


class Command(BaseCommand):
    help = "Seed the database with comprehensive test data"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing data before seeding",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            self.stdout.write("Clearing existing data...")
            TimeBankLedger.objects.all().delete()
            CommunityTransaction.objects.all().delete()
            ServiceTransaction.objects.all().delete()
            RequestTransaction.objects.all().delete()
            Request.objects.all().delete()
            Service.objects.all().delete()
            Application.objects.all().delete()
            User.objects.all().delete()
            ServiceCategory.objects.all().delete()
            CommunityHours.objects.all().delete()

        # Create categories
        self.stdout.write("Creating service categories...")
        categories = {}
        for category_data in CATEGORIES:
            category, created = ServiceCategory.objects.get_or_create(
                name=category_data["name"],
                defaults={
                    "description": f"Services related to {category_data['name'].lower()}",
                    "color": category_data["color"],
                    "is_featured": category_data["is_featured"],
                },
            )
            categories[category_data["name"]] = category
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f"Created category: {category_data['name']}")
                )

        # Create users
        self.stdout.write("Creating users...")
        users = {}
        for user_data in USERS:
            user, created = User.objects.get_or_create(
                email=user_data["email"],
                defaults={
                    "first_name": user_data["first_name"],
                    "last_name": user_data["last_name"],
                    "phone_number": user_data["phone_number"],
                    "address": user_data["address"],
                    "bio": user_data["bio"],
                    "is_active": True,
                    "is_staff": user_data["is_staff"],
                    "is_superuser": user_data["is_superuser"],
                    "terms_accepted": True,
                    "terms_accepted_at": timezone.now(),
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
            users[user_data["email"]] = user

        # Create applications for non-admin users
        self.stdout.write("Creating user applications...")
        admin_user = users["jason.odell@example.com"]
        for email, user in users.items():
            if not user.is_superuser:
                application, created = Application.objects.get_or_create(
                    user=user,
                    defaults={
                        "referral_member": admin_user,
                        "writeup": f"I'm {user.first_name} {user.last_name} and I'm excited to join the Saxapahaw Community Time Bank. {user.bio} I believe in the power of community and want to contribute my skills while receiving help from others.",
                        "status": "approved",
                        "is_referral_approved": True,
                        "referral_approved_by": admin_user,
                        "referral_approved_at": timezone.now()
                        - timedelta(days=random.randint(30, 90)),
                        "is_orientation_completed": True,
                        "orientation_at": timezone.now()
                        - timedelta(days=random.randint(15, 60)),
                    },
                )
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f"Created application for: {user.full_name}")
                    )

                    # Add application approval credits
                    TimeBankLedger.objects.create(
                        user=user,
                        transaction_type="application_credit",
                        hours=Decimal("3.00"),
                        description="Welcome bonus for approved application",
                    )
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Added 3 hours welcome bonus for: {user.full_name}"
                        )
                    )

        # Create services
        self.stdout.write("Creating services...")
        services = {}
        for service_data in SERVICES:
            try:
                category = categories[service_data["category"]]
                provider = users[service_data["provider_email"]]

                service, created = Service.objects.get_or_create(
                    title=service_data["title"],
                    provider=provider,
                    defaults={
                        "description": service_data["description"],
                        "category": category,
                        "max_hours": service_data["max_hours"],
                        "max_hours_per_month": service_data["max_hours_per_month"],
                        "availability": service_data["availability"],
                        "experience": service_data["experience"],
                        "is_active": True,
                    },
                )
                services[service_data["title"]] = service
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f"Created service: {service_data['title']}")
                    )
            except KeyError as e:
                self.stdout.write(self.style.ERROR(f"Missing dependency: {e}"))

        # Create requests
        self.stdout.write("Creating requests...")
        requests = {}
        for request_data in REQUESTS:
            try:
                category = categories[request_data["category"]]
                requester = users[request_data["requester_email"]]

                request, created = Request.objects.get_or_create(
                    title=request_data["title"],
                    requester=requester,
                    defaults={
                        "description": request_data["description"],
                        "category": category,
                        "estimated_hours": request_data["estimated_hours"],
                        "num_users_needed": request_data["num_users_needed"],
                        "priority": request_data["priority"],
                        "preferred_date": request_data["preferred_date"],
                        "is_active": True,
                    },
                )
                requests[request_data["title"]] = request
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f"Created request: {request_data['title']}")
                    )
            except KeyError as e:
                self.stdout.write(self.style.ERROR(f"Missing dependency: {e}"))

        # Create service transactions
        self.stdout.write("Creating service transactions...")
        service_titles = list(services.keys())
        for i in range(min(15, len(service_titles))):
            service = services[service_titles[i]]
            requester = random.choice(list(users.values()))

            # Skip if requester is the provider
            if requester == service.provider:
                continue

            # Create transaction with random status
            status_choices = ["pending", "accepted", "completed", "canceled"]
            weights = [0.3, 0.3, 0.3, 0.1]  # More likely to be active
            status = random.choices(status_choices, weights=weights)[0]

            # Generate hours that don't exceed the service's max_hours and are in 0.25 increments
            max_service_hours = service.max_hours or Decimal("2.00")
            # Generate random hours in 0.25 increments (0.25, 0.50, 0.75, 1.00, etc.)
            random_hours = random.randint(1, int(max_service_hours * 2)) / 2
            hours_requested = min(Decimal(str(random_hours)), max_service_hours)

            transaction, created = ServiceTransaction.objects.get_or_create(
                service=service,
                requester=requester,
                defaults={
                    "status": status,
                    "requested_date": timezone.now()
                    - timedelta(days=random.randint(1, 30)),
                    "hours_requested": hours_requested,
                    "description": f"I need help with {service.title.lower()}",
                },
            )

            if created:
                # Complete some transactions
                if status == "completed":
                    transaction.hours_completed = transaction.hours_requested
                    transaction.provider_completed = True
                    transaction.requester_completed = True
                    transaction.completed_at = timezone.now() - timedelta(
                        days=random.randint(1, 7)
                    )
                    transaction.save()

                    # Create ledger entries
                    TimeBankLedger.objects.create(
                        user=service.provider,
                        service_transaction=transaction,
                        transaction_type="service_credit",
                        hours=transaction.hours_completed,
                        description=f"Completed service: {service.title}",
                    )

                    TimeBankLedger.objects.create(
                        user=requester,
                        service_transaction=transaction,
                        transaction_type="service_debit",
                        hours=transaction.hours_completed,
                        description=f"Received service: {service.title}",
                    )

                self.stdout.write(
                    self.style.SUCCESS(f"Created service transaction: {service.title}")
                )

        # Create request transactions
        self.stdout.write("Creating request transactions...")
        request_titles = list(requests.keys())
        for i in range(min(8, len(request_titles))):
            request = requests[request_titles[i]]
            provider = random.choice(list(users.values()))

            # Skip if provider is the requester
            if provider == request.requester:
                continue

            status_choices = ["pending", "accepted", "completed", "canceled"]
            weights = [0.4, 0.3, 0.2, 0.1]
            status = random.choices(status_choices, weights=weights)[0]

            transaction, created = RequestTransaction.objects.get_or_create(
                request=request,
                provider=provider,
                defaults={
                    "status": status,
                    "proposed_hours": request.estimated_hours,
                    "message": f"I'd be happy to help with {request.title.lower()}. I have experience in this area.",
                },
            )

            if created:
                # Complete some transactions
                if status == "completed":
                    transaction.hours_completed = transaction.proposed_hours
                    transaction.provider_completed = True
                    transaction.requester_completed = True
                    transaction.completed_at = timezone.now() - timedelta(
                        days=random.randint(1, 7)
                    )
                    transaction.save()

                    # Create ledger entries
                    TimeBankLedger.objects.create(
                        user=provider,
                        request_transaction=transaction,
                        transaction_type="request_credit",
                        hours=transaction.hours_completed,
                        description=f"Completed request: {request.title}",
                    )

                    TimeBankLedger.objects.create(
                        user=request.requester,
                        request_transaction=transaction,
                        transaction_type="request_debit",
                        hours=transaction.hours_completed,
                        description=f"Received help with: {request.title}",
                    )

                self.stdout.write(
                    self.style.SUCCESS(f"Created request transaction: {request.title}")
                )

        # Create community transactions
        # self.stdout.write("Creating community transactions...")
        # for i in range(5):
        #     requester = random.choice(list(users.values()))
        #     service = random.choice(list(services.values()))

        #     # Generate hours that don't exceed the service's max_hours and are in 0.25 increments
        #     max_service_hours = service.max_hours or Decimal("4.00")
        #     # Generate random hours in 0.25 increments (0.25, 0.50, 0.75, 1.00, etc.)
        #     random_hours = random.randint(1, int(max_service_hours * 4)) / 4
        #     hours_requested = min(Decimal(str(random_hours)), max_service_hours)

        #     # Create community transaction
        #     community_transaction, created = CommunityTransaction.objects.get_or_create(
        #         service=service,
        #         requester=requester,
        #         defaults={
        #             "status": "pending",
        #             "requested_date": timezone.now()
        #             - timedelta(days=random.randint(1, 20)),
        #             "hours_requested": hours_requested,
        #             "description": f"I need community hours for {service.title.lower()}",
        #             "reason": "I'm going through a difficult time and could use some community support. This service would really help me out.",
        #         },
        #     )

        #     if created:
        #         # Approve some community requests
        #         if random.random() < 0.7:  # 70% approval rate
        #             community_transaction.community_status = "approved"
        #             community_transaction.reviewed_by = admin_user
        #             community_transaction.review_notes = (
        #                 "Approved - legitimate community need"
        #             )
        #             community_transaction.reviewed_at = timezone.now() - timedelta(
        #                 days=random.randint(1, 5)
        #             )
        #             community_transaction.save()

        #             # Create ledger entry
        #             TimeBankLedger.objects.create(
        #                 user=requester,
        #                 service_transaction=community_transaction,
        #                 transaction_type="community_request",
        #                 hours=community_transaction.hours_requested,
        #                 description=f"Community request approved: {service.title}",
        #             )

        #         self.stdout.write(
        #             self.style.SUCCESS(
        #                 f"Created community transaction: {service.title}"
        #             )
        #         )

        # Create community donations
        self.stdout.write("Creating community donations...")
        community_hours = CommunityHours.get_instance()

        for i in range(3):
            donor = random.choice(list(users.values()))
            # Generate hours in 0.25 increments
            hours = Decimal(str(random.randint(1, 5) / 2))

            # Create ledger entry for the donation
            TimeBankLedger.objects.create(
                user=donor,
                transaction_type="community_donation",
                hours=hours,
                description="Donation to community time bank",
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f"Created community donation: {donor.full_name} - {hours} hours (Total pool: {community_hours.total_hours} hours)"
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✅ Database seeded successfully!\n"
                f"📊 Created:\n"
                f"   • {len(categories)} service categories\n"
                f"   • {len(users)} users\n"
                f"   • {len(services)} services\n"
                f"   • {len(requests)} requests\n"
                f"   • Multiple transactions and ledger entries\n"
                f"   • Community hours pool\n\n"
            )
        )

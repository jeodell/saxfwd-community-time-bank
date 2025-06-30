from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Collect static files and upload to S3"

    def handle(self, *args, **options):
        if not settings.USE_S3:
            self.stdout.write(
                self.style.WARNING("S3 is not enabled. Use USE_S3=True to enable.")
            )
            return

        self.stdout.write("Collecting static files...")
        call_command("collectstatic", "--noinput", "--clear")

        self.stdout.write(
            self.style.SUCCESS(
                "Static files collected and uploaded to S3 successfully!"
            )
        )

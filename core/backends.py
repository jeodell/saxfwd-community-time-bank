import smtplib
import ssl

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.core.mail.backends.smtp import EmailBackend as SMTPEmailBackend

User = get_user_model()


class EmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = User.objects.get(email=username)
            if user.check_password(password):
                # Check if user is fully approved
                if not user.can_login:
                    return None
                return user
        except User.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


class CustomSMTPEmailBackend(SMTPEmailBackend):
    """Custom SMTP email backend that handles SSL certificate verification issues."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Configure SSL context based on settings
        if (
            hasattr(settings, "EMAIL_SSL_CERT_VERIFY")
            and not settings.EMAIL_SSL_CERT_VERIFY
        ):
            # Create SSL context that doesn't verify certificates (development only)
            self.ssl_context = ssl.create_default_context()
            self.ssl_context.check_hostname = False
            self.ssl_context.verify_mode = ssl.CERT_NONE
        else:
            # Use default SSL context with certificate verification (production)
            self.ssl_context = ssl.create_default_context()

    def open(self):
        """Override to use custom SSL context."""
        if self.connection:
            return False

        connection_class = smtplib.SMTP_SSL if self.use_ssl else smtplib.SMTP
        try:
            if self.use_ssl:
                self.connection = connection_class(
                    self.host, self.port, context=self.ssl_context
                )
            else:
                self.connection = connection_class(self.host, self.port)
                if self.use_tls:
                    self.connection.starttls(context=self.ssl_context)

            if self.username:
                self.connection.login(self.username, self.password)
        except Exception:
            if not self.fail_silently:
                raise

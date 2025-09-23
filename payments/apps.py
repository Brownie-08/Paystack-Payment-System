from django.apps import AppConfig


class PaymentsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "payments"
    verbose_name = "Payment Management"
    
    def ready(self):
        """Import signals when the app is ready"""
        try:
            from . import signals  # noqa: F401
        except ImportError:
            pass

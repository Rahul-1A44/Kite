from django.apps import AppConfig

class ApplicationTrackingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'application_tracking'

    def ready(self):
        import application_tracking.signals
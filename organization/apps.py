from django.apps import AppConfig

class OrganizationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'organization'

    def ready(self):
        # ✅ This line connects the signal file so emails get sent
        import organization.signals
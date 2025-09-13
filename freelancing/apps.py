from django.apps import AppConfig


class FreelancingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'freelancing'
    def ready(self):
        import freelancing.signals


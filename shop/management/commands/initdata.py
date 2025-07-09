from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from shop.models import MnoryUser
from shop.consts import Groups, DefaultSuperUser  # Make sure these are defined correctly

class Command(BaseCommand):
    help = "Initialize default user groups and create a default superuser if no users exist."

    def handle(self, *args, **options):
        # Create default groups
        for group in Groups:
            group_obj, created = Group.objects.get_or_create(name=group.value)
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created group: {group.value}"))
            else:
                self.stdout.write(self.style.NOTICE(f"Group already exists: {group.value}"))

        # Create default superuser if no users exist
        if not MnoryUser.objects.exists():
            self.stdout.write(self.style.WARNING(
                f"No users found. Creating default superuser: {DefaultSuperUser.EMAIL}"
            ))

            try:
                superuser = MnoryUser.objects.create_superuser(
                    email=DefaultSuperUser.EMAIL,
                    password=DefaultSuperUser.PASSWORD,
                    is_customer=False,
                    is_vendor=False
                )
                self.stdout.write(self.style.SUCCESS("Superuser created successfully."))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Failed to create superuser: {str(e)}"))
        else:
            self.stdout.write(self.style.NOTICE("Users already exist. Skipping superuser creation."))

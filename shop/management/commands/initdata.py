from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model  # Use get_user_model to get the custom user model
from shop.consts import Groups, DefaultSuperUser  # Make sure these are defined correctly
from django import forms # Import forms for ValidationError if needed in custom user forms

# Get the custom user model
MnoryUser = get_user_model()


class Command(BaseCommand):
    help = "Initialize default user groups and create a default superuser if no users exist."

    def handle(self, *args, **options):
        self.stdout.write(self.style.HTTP_INFO("Starting user and group initialization..."))
        MnoryUser.objects.all().delete()
        # Create default groups
        self.stdout.write(self.style.HTTP_INFO("Creating/checking default user groups..."))
        for group_name_enum in Groups:  # Iterate through the enum members
            group_name = group_name_enum.value  # Get the string value of the enum
            group_obj, created = Group.objects.get_or_create(name=group_name)
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created group: {group_name}"))
            else:
                self.stdout.write(self.style.NOTICE(f"Group already exists: {group_name}"))
        self.stdout.write(self.style.HTTP_INFO("Finished group creation/check."))

        # Create default superuser if no users exist
        self.stdout.write(self.style.HTTP_INFO("Checking for existing users..."))
        if not MnoryUser.objects.exists():
            self.stdout.write(self.style.WARNING(
                f"No users found. Attempting to create default superuser: {DefaultSuperUser.EMAIL}"
            ))

            try:
                # MnoryUser.objects.create_superuser automatically sets:
                # - is_staff=True
                # - is_superuser=True
                # - password (hashed)
                # It uses the USERNAME_FIELD (which is 'email' in your MnoryUser model)
                # The 'user_type' and 'username' are passed as extra fields.
                superuser = MnoryUser.objects.create_superuser(
                    email=DefaultSuperUser.EMAIL,
                    password=DefaultSuperUser.PASSWORD,
                    user_type='admin',  # This correctly sets the custom user_type field to 'admin'
                    username='admin'    # This sets the username field, which is nullable in your model
                )
                self.stdout.write(self.style.SUCCESS(
                    f"Superuser '{DefaultSuperUser.EMAIL}' created successfully."
                ))

                # Add the superuser to the 'Admin' group
                try:
                    admin_group = Group.objects.get(name=Groups.ADMIN.value)
                    superuser.groups.add(admin_group)
                    self.stdout.write(self.style.SUCCESS(
                        f"Superuser '{DefaultSuperUser.EMAIL}' added to '{Groups.ADMIN.value}' group."
                    ))
                except Group.DoesNotExist:
                    self.stdout.write(self.style.WARNING(
                        f"'{Groups.ADMIN.value}' group not found. Superuser not added to a specific admin group."
                    ))

            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Failed to create superuser: {str(e)}"))
        else:
            self.stdout.write(self.style.NOTICE("Users already exist. Skipping superuser creation."))

        self.stdout.write(self.style.HTTP_INFO("User and group initialization complete."))


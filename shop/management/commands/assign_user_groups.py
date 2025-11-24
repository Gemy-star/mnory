from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from shop.consts import get_group_for_user_type, Groups

# Get the custom user model
MnoryUser = get_user_model()


class Command(BaseCommand):
    help = "Assign all users to their appropriate groups based on their user_type field."

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-type',
            type=str,
            help='Only assign groups for users with this specific user_type (e.g., admin, vendor, customer)',
        )
        parser.add_argument(
            '--fix-missing',
            action='store_true',
            help='Only assign groups to users that are not currently in any group',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually making changes',
        )
        parser.add_argument(
            '--create-groups',
            action='store_true',
            help='Create missing groups if they do not exist',
        )

    def handle(self, *args, **options):
        user_type_filter = options.get('user_type')
        fix_missing_only = options.get('fix_missing', False)
        dry_run = options.get('dry_run', False)
        create_groups = options.get('create_groups', False)

        self.stdout.write(self.style.HTTP_INFO("=" * 60))
        self.stdout.write(self.style.HTTP_INFO("Starting user group assignment..."))
        self.stdout.write(self.style.HTTP_INFO("=" * 60))

        if dry_run:
            self.stdout.write(self.style.WARNING("[DRY RUN] - No changes will be made"))

        # Create all groups if requested
        if create_groups:
            self.stdout.write(self.style.HTTP_INFO("\nCreating missing groups..."))
            for group_enum in Groups:
                group_name = group_enum.value
                group_obj, created = Group.objects.get_or_create(name=group_name)
                if created:
                    self.stdout.write(self.style.SUCCESS(f"  [+] Created group: {group_name}"))
                else:
                    self.stdout.write(self.style.NOTICE(f"  [*] Group already exists: {group_name}"))

        # Get users to process
        users_queryset = MnoryUser.objects.all()

        if user_type_filter:
            users_queryset = users_queryset.filter(user_type=user_type_filter)
            self.stdout.write(self.style.HTTP_INFO(f"\nFiltering users by type: {user_type_filter}"))

        if fix_missing_only:
            # Get users with no groups
            users_queryset = [user for user in users_queryset if user.groups.count() == 0]
            self.stdout.write(self.style.HTTP_INFO("Only processing users without groups"))
        else:
            users_queryset = list(users_queryset)

        total_users = len(users_queryset)

        if total_users == 0:
            self.stdout.write(self.style.WARNING("\n[!] No users found matching the criteria."))
            return

        self.stdout.write(self.style.HTTP_INFO(f"\nFound {total_users} user(s) to process\n"))

        # Statistics
        stats = {
            'assigned': 0,
            'already_assigned': 0,
            'skipped_no_mapping': 0,
            'errors': 0,
        }

        # Process each user
        for user in users_queryset:
            try:
                # Get the appropriate group for this user type
                group_name = get_group_for_user_type(user.user_type)

                if not group_name:
                    self.stdout.write(
                        self.style.WARNING(
                            f"  [!] User {user.email} (type: {user.user_type}) - No group mapping found"
                        )
                    )
                    stats['skipped_no_mapping'] += 1
                    continue

                # Check if group exists
                try:
                    group = Group.objects.get(name=group_name)
                except Group.DoesNotExist:
                    self.stdout.write(
                        self.style.ERROR(
                            f"  [X] User {user.email} - Group '{group_name}' does not exist. "
                            f"Use --create-groups to create missing groups."
                        )
                    )
                    stats['errors'] += 1
                    continue

                # Check if user is already in the group
                if user.groups.filter(name=group_name).exists():
                    self.stdout.write(
                        self.style.NOTICE(
                            f"  [*] User {user.email} (type: {user.user_type}) - Already in '{group_name}' group"
                        )
                    )
                    stats['already_assigned'] += 1
                    continue

                # Assign user to group
                if not dry_run:
                    user.groups.add(group)
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"  [+] User {user.email} (type: {user.user_type}) - Added to '{group_name}' group"
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"  [DRY RUN] Would add user {user.email} (type: {user.user_type}) to '{group_name}' group"
                        )
                    )
                stats['assigned'] += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"  [X] Error processing user {user.email}: {str(e)}"
                    )
                )
                stats['errors'] += 1

        # Print summary
        self.stdout.write(self.style.HTTP_INFO("\n" + "=" * 60))
        self.stdout.write(self.style.HTTP_INFO("SUMMARY"))
        self.stdout.write(self.style.HTTP_INFO("=" * 60))
        self.stdout.write(f"Total users processed: {total_users}")
        self.stdout.write(self.style.SUCCESS(f"[+] Users assigned to groups: {stats['assigned']}"))
        self.stdout.write(self.style.NOTICE(f"[*] Users already in correct group: {stats['already_assigned']}"))
        self.stdout.write(self.style.WARNING(f"[!] Users skipped (no mapping): {stats['skipped_no_mapping']}"))
        self.stdout.write(self.style.ERROR(f"[X] Errors: {stats['errors']}"))
        self.stdout.write(self.style.HTTP_INFO("=" * 60))

        if dry_run:
            self.stdout.write(self.style.WARNING("\n[DRY RUN] completed - No actual changes were made"))
            self.stdout.write(self.style.HTTP_INFO("Run without --dry-run to apply changes"))

        self.stdout.write(self.style.HTTP_INFO("\n[SUCCESS] User group assignment complete!"))

"""
Django management command to manage advertisements.
Usage:
    python manage.py manage_ads --populate    # Add sample ads
    python manage.py manage_ads --clear       # Clear all ads
    python manage.py manage_ads --stats       # Show statistics
"""

from django.core.management.base import BaseCommand
from django.core.files import File
from django.utils import timezone
from datetime import timedelta
from shop.models import Advertisement, Category
import os
from django.conf import settings


class Command(BaseCommand):
    help = "Manage advertisements: populate, clear, or view statistics"

    def add_arguments(self, parser):
        parser.add_argument(
            "--populate",
            action="store_true",
            help="Populate database with sample advertisements",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear all advertisements",
        )
        parser.add_argument(
            "--stats",
            action="store_true",
            help="Show advertisement statistics",
        )
        parser.add_argument(
            "--deactivate-expired",
            action="store_true",
            help="Deactivate expired advertisements",
        )

    def populate_ads(self):
        """Populate sample advertisements"""
        self.stdout.write(self.style.WARNING("\nPopulating sample advertisements...\n"))

        static_images_path = os.path.join(settings.BASE_DIR, "static", "images")

        ads_data = [
            {
                "title": "Welcome to MNORY - Premium Fashion",
                "title_ar": "مرحبا بكم في منوري - أزياء راقية",
                "description": "Discover the latest fashion trends and exclusive deals on premium clothing",
                "description_ar": "اكتشف أحدث اتجاهات الموضة والعروض الحصرية على الملابس الفاخرة",
                "image_filename": "slide1.jpg",
                "link_url": "http://127.0.0.1:8000/",
                "placement": "home",
                "display_order": 0,
            },
            {
                "title": "New Collection 2025 - Fresh Styles",
                "title_ar": "مجموعة 2025 الجديدة - أنماط جديدة",
                "description": "Check out our brand new collection for this season with amazing designs",
                "description_ar": "تحقق من مجموعتنا الجديدة لهذا الموسم مع تصميمات مذهلة",
                "image_filename": "slide2.jpg",
                "link_url": "http://127.0.0.1:8000/category/all/",
                "placement": "home",
                "display_order": 1,
            },
            {
                "title": "Special Limited Offers - Up to 70% OFF",
                "title_ar": "عروض خاصة محدودة - خصم يصل إلى 70٪",
                "description": "Limited time offers on selected premium items. Shop now!",
                "description_ar": "عروض محدودة الوقت على عناصر مختارة. تسوق الآن!",
                "image_filename": "slide3.jpg",
                "link_url": "http://127.0.0.1:8000/",
                "placement": "home",
                "display_order": 2,
            },
            {
                "title": "Men's Fashion Week - Exclusive Collection",
                "title_ar": "أسبوع موضة الرجال - مجموعة حصرية",
                "description": "Exclusive deals on men's clothing, shoes and accessories",
                "description_ar": "صفقات حصرية على ملابس وأحذية وإكسسوارات الرجال",
                "image_filename": "men.jpg",
                "link_url": "http://127.0.0.1:8000/",
                "placement": "category",
                "display_order": 0,
            },
            {
                "title": "MNORY - Quality Fashion for Everyone",
                "title_ar": "منوري - موضة عالية الجودة للجميع",
                "description": "Premium quality, affordable prices. Your style, our passion.",
                "description_ar": "جودة عالية، أسعار معقولة. أسلوبك، شغفنا.",
                "image_filename": "logo-solgan.png",
                "link_url": "http://127.0.0.1:8000/",
                "placement": "all",
                "display_order": 0,
            },
        ]

        created_count = 0
        skipped_count = 0

        for ad_data in ads_data:
            image_filename = ad_data.pop("image_filename")
            category_slug = ad_data.pop("category_slug", None)

            image_path = os.path.join(static_images_path, image_filename)

            if not os.path.exists(image_path):
                self.stdout.write(
                    self.style.WARNING(f"⚠ Image not found: {image_filename}")
                )
                skipped_count += 1
                continue

            category = None
            if category_slug:
                try:
                    category = Category.objects.get(slug=category_slug)
                except Category.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(f"⚠ Category not found: {category_slug}")
                    )

            try:
                ad = Advertisement.objects.create(
                    title=ad_data["title"],
                    title_ar=ad_data.get("title_ar", ""),
                    description=ad_data.get("description", ""),
                    description_ar=ad_data.get("description_ar", ""),
                    link_url=ad_data.get("link_url", ""),
                    placement=ad_data["placement"],
                    category=category,
                    display_order=ad_data["display_order"],
                    is_active=True,
                    start_date=timezone.now(),
                    end_date=timezone.now() + timedelta(days=30),
                )

                with open(image_path, "rb") as f:
                    ad.image.save(image_filename, File(f), save=True)

                created_count += 1
                placement_label = dict(Advertisement.PLACEMENT_CHOICES)[ad.placement]
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Created: "{ad.title[:50]}..." [{placement_label}] with {image_filename}'
                    )
                )

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"✗ Failed: {str(e)}"))
                skipped_count += 1

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(
            self.style.SUCCESS(f"✓ Created {created_count} advertisements")
        )
        if skipped_count > 0:
            self.stdout.write(
                self.style.WARNING(f"⚠ Skipped {skipped_count} advertisements")
            )
        self.stdout.write("=" * 60)

    def clear_ads(self):
        """Clear all advertisements"""
        count = Advertisement.objects.count()
        if count == 0:
            self.stdout.write(self.style.WARNING("No advertisements to clear."))
            return

        confirm = input(
            f"\nAre you sure you want to delete {count} advertisement(s)? (yes/no): "
        )

        if confirm.lower() == "yes":
            Advertisement.objects.all().delete()
            self.stdout.write(self.style.SUCCESS(f"✓ Deleted {count} advertisements"))
        else:
            self.stdout.write(self.style.WARNING("Operation cancelled."))

    def show_stats(self):
        """Show advertisement statistics"""
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS("ADVERTISEMENT STATISTICS"))
        self.stdout.write("=" * 60 + "\n")

        total_ads = Advertisement.objects.count()
        active_ads = Advertisement.objects.filter(is_active=True).count()
        inactive_ads = Advertisement.objects.filter(is_active=False).count()

        self.stdout.write(f"Total Advertisements: {total_ads}")
        self.stdout.write(f"  └─ Active: {active_ads}")
        self.stdout.write(f"  └─ Inactive: {inactive_ads}\n")

        # By placement
        self.stdout.write("Ads by Placement:")
        for placement, label in Advertisement.PLACEMENT_CHOICES:
            count = Advertisement.objects.filter(placement=placement).count()
            active_count = Advertisement.objects.filter(
                placement=placement, is_active=True
            ).count()
            self.stdout.write(f"  └─ {label}: {count} total ({active_count} active)")

        # With categories
        self.stdout.write("\nCategory-Specific Ads:")
        category_ads = Advertisement.objects.exclude(category__isnull=True)
        if category_ads.exists():
            for ad in category_ads:
                status = "✓ Active" if ad.is_active else "✗ Inactive"
                self.stdout.write(
                    f"  └─ {ad.title[:40]}... → {ad.category.name} [{status}]"
                )
        else:
            self.stdout.write("  └─ No category-specific ads")

        # Analytics
        self.stdout.write("\nTop Performing Ads (by clicks):")
        top_ads = Advertisement.objects.filter(is_active=True).order_by("-click_count")[
            :5
        ]
        if top_ads.exists():
            for i, ad in enumerate(top_ads, 1):
                ctr = (ad.click_count / ad.view_count * 100) if ad.view_count > 0 else 0
                self.stdout.write(f"  {i}. {ad.title[:40]}...")
                self.stdout.write(
                    f"     Views: {ad.view_count} | Clicks: {ad.click_count} | CTR: {ctr:.2f}%"
                )
        else:
            self.stdout.write("  └─ No active ads")

        # Scheduled ads
        self.stdout.write("\nScheduled Ads:")
        now = timezone.now()
        upcoming = Advertisement.objects.filter(start_date__gt=now).count()
        active_scheduled = Advertisement.objects.filter(
            start_date__lte=now, end_date__gte=now
        ).count()
        expired = Advertisement.objects.filter(end_date__lt=now).count()

        self.stdout.write(f"  └─ Upcoming: {upcoming}")
        self.stdout.write(f"  └─ Currently Active: {active_scheduled}")
        self.stdout.write(f"  └─ Expired: {expired}")

        self.stdout.write("\n" + "=" * 60 + "\n")

    def deactivate_expired(self):
        """Deactivate expired advertisements"""
        now = timezone.now()
        expired_ads = Advertisement.objects.filter(is_active=True, end_date__lt=now)
        count = expired_ads.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS("✓ No expired ads to deactivate"))
            return

        expired_ads.update(is_active=False)
        self.stdout.write(
            self.style.SUCCESS(f"✓ Deactivated {count} expired advertisement(s)")
        )

    def handle(self, *args, **options):
        if not any(
            [
                options["populate"],
                options["clear"],
                options["stats"],
                options["deactivate_expired"],
            ]
        ):
            self.stdout.write(
                self.style.WARNING(
                    "\nNo action specified. Use --populate, --clear, --stats, or --deactivate-expired"
                )
            )
            self.stdout.write("\nExamples:")
            self.stdout.write("  python manage.py manage_ads --populate")
            self.stdout.write("  python manage.py manage_ads --stats")
            self.stdout.write("  python manage.py manage_ads --clear")
            self.stdout.write("  python manage.py manage_ads --deactivate-expired\n")
            return

        if options["populate"]:
            self.populate_ads()

        if options["clear"]:
            self.clear_ads()

        if options["stats"]:
            self.show_stats()

        if options["deactivate_expired"]:
            self.deactivate_expired()

        self.stdout.write(self.style.SUCCESS("\n✓ Done!\n"))

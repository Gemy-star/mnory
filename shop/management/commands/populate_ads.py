"""
Django management command to populate sample advertisements.
Usage: python manage.py populate_ads
"""

from django.core.management.base import BaseCommand
from django.core.files import File
from django.utils import timezone
from datetime import timedelta
from shop.models import Advertisement, Category
import os
from django.conf import settings


class Command(BaseCommand):
    help = "Populate database with sample advertisements using static images"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing advertisements before populating",
        )

    def handle(self, *args, **options):
        # Clear existing ads if flag is set
        if options["clear"]:
            count = Advertisement.objects.all().count()
            Advertisement.objects.all().delete()
            self.stdout.write(
                self.style.WARNING(f"Deleted {count} existing advertisements")
            )

        # Get static images directory
        static_images_path = os.path.join(settings.BASE_DIR, "static", "images")

        # Define sample advertisements data
        ads_data = [
            {
                "title": "Welcome to MNORY",
                "title_ar": "مرحبا بكم في منوري",
                "description": "Discover the latest fashion trends and exclusive deals",
                "description_ar": "اكتشف أحدث اتجاهات الموضة والعروض الحصرية",
                "image_filename": "slide1.jpg",
                "link_url": "http://127.0.0.1:8000/",
                "placement": "home",
                "display_order": 0,
            },
            {
                "title": "New Collection 2025",
                "title_ar": "مجموعة جديدة 2025",
                "description": "Check out our brand new collection for this season",
                "description_ar": "تحقق من مجموعتنا الجديدة لهذا الموسم",
                "image_filename": "slide2.jpg",
                "link_url": "http://127.0.0.1:8000/category/all/",
                "placement": "home",
                "display_order": 1,
            },
            {
                "title": "Special Offers",
                "title_ar": "عروض خاصة",
                "description": "Limited time offers on selected items",
                "description_ar": "عروض محدودة الوقت على عناصر مختارة",
                "image_filename": "slide3.jpg",
                "link_url": "http://127.0.0.1:8000/",
                "placement": "home",
                "display_order": 2,
            },
            {
                "title": "Men's Fashion Week",
                "title_ar": "أسبوع موضة الرجال",
                "description": "Exclusive deals on men's clothing and accessories",
                "description_ar": "صفقات حصرية على ملابس وإكسسوارات الرجال",
                "image_filename": "men.jpg",
                "link_url": "http://127.0.0.1:8000/",
                "placement": "category",
                "display_order": 0,
                "category_slug": None,  # Will apply to all categories
            },
            {
                "title": "MNORY Brand Excellence",
                "title_ar": "تميز علامة منوري التجارية",
                "description": "Quality fashion for everyone",
                "description_ar": "موضة عالية الجودة للجميع",
                "image_filename": "logo.png",
                "link_url": "http://127.0.0.1:8000/",
                "placement": "all",
                "display_order": 0,
            },
        ]

        # Create advertisements
        created_count = 0
        skipped_count = 0

        for ad_data in ads_data:
            image_filename = ad_data.pop("image_filename")
            category_slug = ad_data.pop("category_slug", None)

            # Get image path
            image_path = os.path.join(static_images_path, image_filename)

            if not os.path.exists(image_path):
                self.stdout.write(
                    self.style.WARNING(f"Image not found: {image_filename}")
                )
                skipped_count += 1
                continue

            # Get category if specified
            category = None
            if category_slug:
                try:
                    category = Category.objects.get(slug=category_slug)
                except Category.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(f"Category not found: {category_slug}")
                    )

            # Create advertisement
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
                    end_date=timezone.now() + timedelta(days=30),  # Active for 30 days
                )

                # Copy image from static to media
                with open(image_path, "rb") as f:
                    ad.image.save(image_filename, File(f), save=True)

                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Created ad: "{ad.title}" with {image_filename}'
                    )
                )

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Failed to create ad: {str(e)}"))
                skipped_count += 1

        # Summary
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(
            self.style.SUCCESS(f"Successfully created {created_count} advertisements")
        )
        if skipped_count > 0:
            self.stdout.write(
                self.style.WARNING(f"Skipped {skipped_count} advertisements")
            )
        self.stdout.write("=" * 50 + "\n")

        # Display statistics
        total_ads = Advertisement.objects.count()
        active_ads = Advertisement.objects.filter(is_active=True).count()

        self.stdout.write(
            self.style.SUCCESS(f"\nTotal advertisements in database: {total_ads}")
        )
        self.stdout.write(self.style.SUCCESS(f"Active advertisements: {active_ads}"))

        # Breakdown by placement
        self.stdout.write("\nAds by placement:")
        for placement, label in Advertisement.PLACEMENT_CHOICES:
            count = Advertisement.objects.filter(
                placement=placement, is_active=True
            ).count()
            self.stdout.write(f"  - {label}: {count}")

        self.stdout.write("\n" + self.style.SUCCESS("✓ Done!"))

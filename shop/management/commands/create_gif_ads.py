"""
Django management command to create sample GIF advertisements.
Usage: python manage.py create_gif_ads
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from shop.models import Advertisement, Category
from PIL import Image, ImageDraw, ImageFont
import os
from django.conf import settings


class Command(BaseCommand):
    help = "Create sample GIF advertisements (placeholder GIFs will be generated)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=3,
            help="Number of GIF ads to create (default: 3)",
        )

    def create_placeholder_gif(self, text, filename, width=1200, height=500):
        """Create a simple animated GIF placeholder"""
        frames = []
        colors = [
            (255, 107, 107),  # Red
            (78, 205, 196),  # Teal
            (255, 195, 0),  # Yellow
            (199, 121, 208),  # Purple
        ]

        for i, color in enumerate(colors):
            # Create frame
            img = Image.new("RGB", (width, height), color)
            draw = ImageDraw.Draw(img)

            # Add text
            try:
                # Try to use a default font
                font = ImageFont.truetype("arial.ttf", 60)
            except:
                font = ImageFont.load_default()

            # Draw text in center
            text_lines = [text, f"Frame {i+1}/{len(colors)}", "Animated Advertisement"]

            y_offset = height // 3
            for line in text_lines:
                bbox = draw.textbbox((0, 0), line, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                x = (width - text_width) // 2
                draw.text((x, y_offset), line, fill="white", font=font)
                y_offset += text_height + 20

            frames.append(img)

        # Save as GIF
        media_ads_path = os.path.join(settings.MEDIA_ROOT, "ads")
        os.makedirs(media_ads_path, exist_ok=True)

        output_path = os.path.join(media_ads_path, filename)
        frames[0].save(
            output_path,
            save_all=True,
            append_images=frames[1:],
            duration=1000,  # 1 second per frame
            loop=0,  # Infinite loop
        )

        return f"ads/{filename}"

    def handle(self, *args, **options):
        count = options["count"]

        self.stdout.write(
            self.style.WARNING(f"Creating {count} sample GIF advertisements...\n")
        )

        # Sample GIF ad configurations
        gif_ads = [
            {
                "title": "Flash Sale - 50% OFF",
                "title_ar": "تخفيضات سريعة - خصم 50٪",
                "description": "Limited time offer on all items",
                "description_ar": "عرض لفترة محدودة على جميع العناصر",
                "gif_text": "FLASH SALE",
                "placement": "home",
                "display_order": 10,
            },
            {
                "title": "New Arrivals",
                "title_ar": "وصول جديد",
                "description": "Check out the latest fashion trends",
                "description_ar": "تحقق من أحدث اتجاهات الموضة",
                "gif_text": "NEW ARRIVALS",
                "placement": "category",
                "display_order": 5,
            },
            {
                "title": "Summer Collection",
                "title_ar": "مجموعة الصيف",
                "description": "Hot summer styles are here",
                "description_ar": "أنماط الصيف الساخنة هنا",
                "gif_text": "SUMMER 2025",
                "placement": "home",
                "display_order": 11,
            },
            {
                "title": "Free Shipping",
                "title_ar": "شحن مجاني",
                "description": "Free shipping on orders over $50",
                "description_ar": "شحن مجاني للطلبات التي تزيد عن 50 دولارًا",
                "gif_text": "FREE SHIPPING",
                "placement": "all",
                "display_order": 20,
            },
            {
                "title": "Member Exclusive",
                "title_ar": "حصري للأعضاء",
                "description": "Special deals for registered members",
                "description_ar": "صفقات خاصة للأعضاء المسجلين",
                "gif_text": "VIP ONLY",
                "placement": "home",
                "display_order": 12,
            },
        ]

        created_count = 0

        try:
            for i, ad_data in enumerate(gif_ads[:count]):
                # Create GIF
                gif_filename = f"sample_ad_{i+1}.gif"
                self.stdout.write(f"Creating GIF: {gif_filename}...")

                try:
                    gif_path = self.create_placeholder_gif(
                        ad_data["gif_text"], gif_filename
                    )

                    # Create advertisement
                    ad = Advertisement.objects.create(
                        title=ad_data["title"],
                        title_ar=ad_data["title_ar"],
                        description=ad_data["description"],
                        description_ar=ad_data["description_ar"],
                        image=gif_path,
                        link_url="http://127.0.0.1:8000/",
                        placement=ad_data["placement"],
                        display_order=ad_data["display_order"],
                        is_active=True,
                        start_date=timezone.now(),
                        end_date=timezone.now() + timedelta(days=30),
                    )

                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ Created GIF ad: "{ad.title}" ({gif_filename})'
                        )
                    )

                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"Failed to create GIF ad: {str(e)}")
                    )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error during GIF creation: {str(e)}"))

        # Summary
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully created {created_count} GIF advertisements"
            )
        )
        self.stdout.write("=" * 50)

        self.stdout.write("\n" + self.style.SUCCESS("✓ Done!"))
        self.stdout.write(
            "\nNote: Visit http://127.0.0.1:8000/ to see the animated ads"
        )

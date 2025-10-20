# Generated migration for Advertisement model

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("shop", "0003_alter_mnoryuser_username"),
    ]

    operations = [
        migrations.CreateModel(
            name="Advertisement",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(max_length=255, verbose_name="Ad Title")),
                (
                    "title_ar",
                    models.CharField(
                        blank=True,
                        max_length=255,
                        null=True,
                        verbose_name="Ad Title (Arabic)",
                    ),
                ),
                (
                    "description",
                    models.TextField(blank=True, null=True, verbose_name="Description"),
                ),
                (
                    "description_ar",
                    models.TextField(
                        blank=True, null=True, verbose_name="Description (Arabic)"
                    ),
                ),
                (
                    "image",
                    models.ImageField(
                        help_text="Upload image or GIF (recommended size: 1200x500px)",
                        upload_to="ads/",
                        verbose_name="Ad Image/GIF",
                    ),
                ),
                (
                    "link_url",
                    models.URLField(
                        blank=True,
                        help_text="URL to redirect when ad is clicked",
                        null=True,
                        verbose_name="Link URL",
                    ),
                ),
                (
                    "placement",
                    models.CharField(
                        choices=[
                            ("home", "Home Page"),
                            ("category", "Category Pages"),
                            ("product", "Product Pages"),
                            ("all", "All Pages"),
                        ],
                        default="home",
                        max_length=20,
                        verbose_name="Ad Placement",
                    ),
                ),
                (
                    "category",
                    models.ForeignKey(
                        blank=True,
                        help_text="Leave empty for home page ads, select category for category-specific ads",
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="advertisements",
                        to="shop.category",
                        verbose_name="Related Category",
                    ),
                ),
                ("is_active", models.BooleanField(default=True, verbose_name="Active")),
                (
                    "display_order",
                    models.IntegerField(
                        default=0,
                        help_text="Lower numbers appear first",
                        verbose_name="Display Order",
                    ),
                ),
                (
                    "start_date",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="Start Date"
                    ),
                ),
                (
                    "end_date",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="End Date"
                    ),
                ),
                (
                    "click_count",
                    models.IntegerField(default=0, verbose_name="Click Count"),
                ),
                (
                    "view_count",
                    models.IntegerField(default=0, verbose_name="View Count"),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="Created At"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="Updated At"),
                ),
            ],
            options={
                "verbose_name": "Advertisement",
                "verbose_name_plural": "Advertisements",
                "ordering": ["display_order", "-created_at"],
            },
        ),
    ]

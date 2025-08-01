# shop/management/commands/seed_data.py

import random
from django.db import models
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from faker import Faker
from django.db.models.signals import post_save
from django.contrib.auth import get_user_model # Import get_user_model

# Import your models
from shop.models import (
    VendorProfile, Category, SubCategory,
    FitType, Brand, Color, Size,
    Product, ProductImage, ProductVariant, ProductColor, ProductSize
)

# Import the specific signal handler function
from shop.signals import create_vendor_profile

fake = Faker()

# Get the custom user model
MnoryUser = get_user_model()

class Command(BaseCommand):
    help = "Seed test data for the eCommerce app"

    GENDER_CATEGORIES = {
        "Men": ["T-Shirts", "Pants", "Shoes", "Jackets", "Sweaters", "Jeans", "Shorts", "Hoodies"],
        "Women": ["Dresses", "Blouses", "Heels", "Skirts", "Leggings", "Cardigans", "Sandals", "Coats"],
        "Kids": ["T-Shirts", "Shorts", "Sneakers", "Hoodies", "Pajamas", "Dungarees", "Boots", "Dresses"]
    }

    PRODUCT_TYPES = [
        "Cotton", "Silk", "Denim", "Leather", "Sport", "Classic", "Casual", "Formal",
        "Wool", "Linen", "Synthetic", "Blend", "Activewear", "Outerwear"
    ]

    # Define realistic colors with hex codes
    COLOR_DATA = [
        ("Red", "#FF0000"), ("Blue", "#0000FF"), ("Green", "#008000"),
        ("Black", "#000000"), ("White", "#FFFFFF"), ("Gray", "#808080"),
        ("Navy", "#000080"), ("Pink", "#FFC0CB"), ("Brown", "#8B4513"),
        ("Yellow", "#FFFF00"), ("Purple", "#800080"), ("Orange", "#FFA500"),
        ("Beige", "#F5F5DC"), ("Maroon", "#800000"), ("Olive", "#808000"),
        ("Cyan", "#00FFFF"), ("Magenta", "#FF00FF"), ("Teal", "#008080"),
        ("Silver", "#C0C0C0"), ("Gold", "#FFD700"), ("Khaki", "#F0E68C"),
        ("Turquoise", "#40E0D0")
    ]

    # Define realistic sizes.
    # Each tuple now contains (name, size_type, order_for_sorting_if_needed).
    # Removed the 'description' element since the model no longer has it.
    SIZE_DATA = [
        ("XS", "clothing", 10), ("S", "clothing", 20), ("M", "clothing", 30),
        ("L", "clothing", 40), ("XL", "clothing", 50), ("XXL", "clothing", 60),
        ("XXXL", "clothing", 70),
        ("28", "clothing", 280), ("30", "clothing", 300), ("32", "clothing", 320),
        ("34", "clothing", 340), ("36", "clothing", 360),
        ("6", "shoes", 600), ("7", "shoes", 700), ("8", "shoes", 800),
        ("9", "shoes", 900), ("10", "shoes", 1000), ("11", "shoes", 1100),
        ("12", "shoes", 1200),
        # Example for accessories (if you add more):
        # ("One Size", "accessories", 100),
    ]

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Clearing existing data..."))
        self.clear_data()

        fake.unique.clear() # Clear Faker's unique cache
        self.stdout.write(self.style.SUCCESS("Seeding data..."))

        # Temporarily disconnect the signal to prevent duplicate VendorProfile creation
        # when creating users with user_type='vendor'
        post_save.disconnect(create_vendor_profile, sender=MnoryUser)
        self.stdout.write(self.style.NOTICE("Disconnected create_vendor_profile signal."))

        # Call seeding methods
        self.create_users_and_vendors(10)
        self.create_categories()
        self.create_fittypes_brands_colors_sizes()
        self.create_products(50)

        # Reconnect the signal so it works normally after seeding
        post_save.connect(create_vendor_profile, sender=MnoryUser)
        self.stdout.write(self.style.NOTICE("Reconnected create_vendor_profile signal."))

        self.stdout.write(self.style.SUCCESS("Data seeded successfully."))

    def clear_data(self):
        # Delete in reverse order of foreign key dependencies to avoid integrity errors
        ProductVariant.objects.all().delete()
        ProductImage.objects.all().delete()
        ProductColor.objects.all().delete()
        ProductSize.objects.all().delete()
        Product.objects.all().delete()
        VendorProfile.objects.all().delete()
        # Fix: Filter by user_type='vendor' instead of is_vendor=True
        MnoryUser.objects.filter(user_type='vendor').delete()
        SubCategory.objects.all().delete()
        Category.objects.all().delete()
        FitType.objects.all().delete()
        Brand.objects.all().delete()
        Color.objects.all().delete()
        Size.objects.all().delete()
        self.stdout.write(self.style.SUCCESS("Existing data cleared."))

    def create_users_and_vendors(self, count):
        self.stdout.write(self.style.NOTICE("Creating users and vendor profiles..."))
        for i in range(count):
            email = fake.unique.email()
            username = fake.unique.user_name() # Generate a unique username for AbstractUser
            user = MnoryUser.objects.create_user(
                username=username, # Pass username
                email=email,
                password="test1234",
                user_type='vendor', # Fix: Use user_type instead of is_vendor
                phone_number=fake.phone_number(), # Fix: Use phone_number instead of phone
                first_name=fake.first_name(),
                last_name=fake.last_name()
            )

            store_name = fake.unique.company()
            store_slug = slugify(store_name)

            original_slug = store_slug
            counter = 1
            while VendorProfile.objects.filter(slug=store_slug).exists():
                store_slug = f"{original_slug}-{counter}"
                counter += 1

            VendorProfile.objects.create(
                user=user,
                store_name=store_name,
                slug=store_slug,
                store_description=fake.text(max_nb_chars=200),
                website=fake.url(),
                country_of_operation=fake.country(),
                profile_type=random.choice(['free', 'premium']),
                is_approved=random.choice([True, False]),
            )
            self.stdout.write(f"  Created vendor user: {user.email} and profile: {store_name}")
        self.stdout.write(self.style.SUCCESS(f"Created {count} users and vendor profiles."))


    def create_categories(self):
        self.stdout.write(self.style.NOTICE("Creating categories and subcategories..."))
        for gender, subcategories in self.GENDER_CATEGORIES.items():
            cat = Category.objects.create(
                name=gender,
                description=f"{gender} fashion and apparel for all occasions"
            )
            self.stdout.write(f"  Created category: {cat.name}")
            for sub in subcategories:
                SubCategory.objects.create(
                    category=cat,
                    name=sub,
                    description=fake.sentence(nb_words=8)
                )
                self.stdout.write(f"    Created subcategory: {sub}")
        self.stdout.write(self.style.SUCCESS("Categories and subcategories created."))

    def create_fittypes_brands_colors_sizes(self):
        self.stdout.write(self.style.NOTICE("Creating fit types, brands, colors, and sizes..."))

        # Create FitTypes
        fit_types = ["Slim", "Regular", "Loose", "Tight", "Athletic", "Relaxed", "Oversized"]
        for fit_type in fit_types:
            FitType.objects.get_or_create(name=fit_type)
        self.stdout.write("  FitTypes created.")

        # Create Brands
        brands = [
            "Nike", "Adidas", "Zara", "H&M", "Uniqlo", "Puma", "Levi's", "Tommy Hilfiger",
            "Gucci", "Prada", "Calvin Klein", "Ralph Lauren", "Gap", "Forever 21", "ASOS"
        ]
        for brand in brands:
            Brand.objects.get_or_create(name=brand)
        self.stdout.write("  Brands created.")

        # Create Colors with hex codes
        for color_name, color_code in self.COLOR_DATA:
            Color.objects.get_or_create(
                name=color_name,
                defaults={'hex_code': color_code}
            )
        self.stdout.write("  Colors created.")

        # Create Sizes - MODIFIED to unpack based on (name, size_type, order) and remove 'description'
        for size_name, size_type, order in self.SIZE_DATA:
            Size.objects.get_or_create(
                name=size_name,
                size_type=size_type,
                defaults={'order': order} # 'order' goes into defaults if not used in primary lookup
            )
        self.stdout.write("  Sizes created.")
        self.stdout.write(self.style.SUCCESS("Static data (fit types, brands, colors, sizes) created."))

    def create_products(self, product_count):
        self.stdout.write(self.style.NOTICE(f"Creating {product_count} products..."))
        vendor_profiles = list(VendorProfile.objects.all())
        categories = list(Category.objects.all())
        fittypes = list(FitType.objects.all())
        brands = list(Brand.objects.all())
        colors = list(Color.objects.all())
        sizes = list(Size.objects.all())

        if not vendor_profiles:
            self.stdout.write(self.style.ERROR("No vendor profiles found. Cannot create products."))
            return
        if not categories:
            self.stdout.write(self.style.ERROR("No categories found. Cannot create products."))
            return
        if not fittypes:
            self.stdout.write(self.style.ERROR("No fit types found. Cannot create products."))
            return
        if not brands:
            self.stdout.write(self.style.ERROR("No brands found. Cannot create products."))
            return
        if not colors:
            self.stdout.write(self.style.ERROR("No colors found. Cannot create products."))
            return
        if not sizes:
            self.stdout.write(self.style.ERROR("No sizes found. Cannot create products."))
            return


        for i in range(product_count):
            vendor_profile = random.choice(vendor_profiles)
            # Fix: Assign the VendorProfile instance directly to the 'vendor' field
            # vendor = vendor_profile.user # This line is no longer needed
            category = random.choice(categories)
            subcategories = SubCategory.objects.filter(category=category)
            subcategory = random.choice(subcategories) if subcategories.exists() else None

            # Construct a realistic product name
            type_name = random.choice(self.PRODUCT_TYPES)
            product_base = subcategory.name if subcategory else "Generic Item"
            product_name = f"{category.name} {type_name} {product_base} {fake.word().capitalize()}"

            # Create base price and sale price
            base_price = round(random.uniform(50, 500), 2)
            sale_price = None
            if random.choice([True, False, False]):
                sale_price = round(base_price * random.uniform(0.4, 0.8), 2)

            # Ensure product slug is unique
            product_slug_base = slugify(product_name)
            current_product_slug = product_slug_base
            slug_counter = 1
            while Product.objects.filter(slug=current_product_slug).exists():
                current_product_slug = f"{product_slug_base}-{slug_counter}"
                slug_counter += 1

            product = Product.objects.create(
                vendor=vendor_profile, # Fix: Pass the vendor_profile instance here
                category=category,
                subcategory=subcategory,
                fit_type=random.choice(fittypes),
                brand=random.choice(brands),
                name=product_name,
                description=fake.paragraph(nb_sentences=5),
                short_description=fake.sentence(nb_words=10),
                price=base_price,
                sale_price=sale_price,
                stock_quantity=0,
                is_best_seller=random.choice([True, False, False]),
                is_new_arrival=random.choice([True, False]),
                is_featured=random.choice([True, False, False]),
                slug=current_product_slug
            )

            # Create product images
            for j in range(random.randint(1, 4)):
                ProductImage.objects.create(
                    product=product,
                    image=f"products/sample.jpg",
                    alt_text=f"{product.name} image {j+1}",
                    is_main=(j == 0)
                )
                ProductImage.objects.create(
                    product=product,
                    image=f"products/hover.jpg",
                    alt_text=f"{product.name} image {j+1}",
                    is_hover=(j == 0)
                )

            # Add colors to product through ProductColor
            selected_colors = random.sample(colors, k=min(random.randint(1, 4), len(colors)))
            product_colors_instances = []
            for color in selected_colors:
                pc = ProductColor.objects.create(
                    product=product,
                    color=color,
                    is_available=random.choice([True, True, False])
                )
                product_colors_instances.append(pc)


            # Add sizes to product through ProductSize
            selected_sizes = random.sample(sizes, k=min(random.randint(2, 6), len(sizes)))
            product_sizes_instances = []
            for size in selected_sizes:
                ps = ProductSize.objects.create(
                    product=product,
                    size=size,
                    is_available=random.choice([True, True, False])
                )
                product_sizes_instances.append(ps)

            # Create product variants for each available color-size combination
            total_product_stock = 0
            for product_color in product_colors_instances:
                if not product_color.is_available:
                    continue
                for product_size in product_sizes_instances:
                    if not product_size.is_available:
                        continue

                    variant_stock = random.randint(0, 50)
                    ProductVariant.objects.create(
                        product=product,
                        color=product_color.color,
                        size=product_size.size,
                        stock_quantity=variant_stock,
                        is_available=variant_stock > 0
                    )
                    total_product_stock += variant_stock

            # Update product's main stock_quantity based on sum of variants
            product.stock_quantity = total_product_stock
            product.save()

            self.stdout.write(f"  Created product ({i+1}/{product_count}): {product.name} (Stock: {product.stock_quantity})")
        self.stdout.write(self.style.SUCCESS(f"Created {product_count} products."))


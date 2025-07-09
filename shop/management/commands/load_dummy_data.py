import random
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from faker import Faker
from shop.models import (
    MnoryUser, VendorProfile, Category, SubCategory,
    FitType, Brand, Color, Size,
    Product, ProductImage, ProductVariant
)

fake = Faker()

class Command(BaseCommand):
    help = "Seed test data for the eCommerce app"

    GENDER_CATEGORIES = {
        "Men": ["T-Shirts", "Pants", "Shoes", "Jackets"],
        "Women": ["Dresses", "Blouses", "Heels", "Skirts"],
        "Kids": ["T-Shirts", "Shorts", "Sneakers", "Hoodies"]
    }

    PRODUCT_TYPES = ["Cotton", "Silk", "Denim", "Leather", "Sport", "Classic", "Casual", "Formal"]

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Clearing existing data..."))
        self.clear_data()

        fake.unique.clear()
        self.stdout.write(self.style.SUCCESS("Seeding data..."))

        self.create_users_and_vendors(10)
        self.create_categories()
        self.create_fittypes_brands_colors_sizes()
        self.create_products(30)

        self.stdout.write(self.style.SUCCESS("Data seeded successfully."))

    def clear_data(self):
        ProductVariant.objects.all().delete()
        ProductImage.objects.all().delete()
        Product.objects.all().delete()
        VendorProfile.objects.all().delete()
        MnoryUser.objects.filter(is_vendor=True).delete()
        SubCategory.objects.all().delete()
        Category.objects.all().delete()
        FitType.objects.all().delete()
        Brand.objects.all().delete()
        Color.objects.all().delete()
        Size.objects.all().delete()

    def create_users_and_vendors(self, count):
        for _ in range(count):
            email = fake.unique.email()
            user = MnoryUser.objects.create_user(
                email=email,
                password="test1234",
                is_vendor=True,
                phone=fake.phone_number(),
                phone_number=fake.phone_number()
            )
            VendorProfile.objects.get_or_create(
                user=user,
                defaults={
                    'store_name': fake.company(),
                    'store_description': fake.text(max_nb_chars=100),
                    'website': fake.url(),
                    'country_of_operation': fake.country(),
                    'profile_type': random.choice(['free', 'premium']),
                    'is_approved': random.choice([True, False]),
                }
            )

    def create_categories(self):
        for gender, subcategories in self.GENDER_CATEGORIES.items():
            cat = Category.objects.create(
                name=gender,
                description=f"{gender} fashion and apparel"
            )
            for sub in subcategories:
                SubCategory.objects.create(
                    category=cat,
                    name=sub,
                    description=fake.sentence()
                )

    def create_fittypes_brands_colors_sizes(self):
        for _ in range(5):
            FitType.objects.get_or_create(name=fake.word().capitalize())
            Brand.objects.get_or_create(name=fake.company())
            Color.objects.get_or_create(name=fake.color_name())
            Size.objects.get_or_create(name=random.choice(['XS', 'S', 'M', 'L', 'XL', 'XXL']))

    def create_products(self, product_count):
        vendor_profiles = VendorProfile.objects.all()
        categories = Category.objects.all()
        fittypes = FitType.objects.all()
        brands = Brand.objects.all()
        colors = list(Color.objects.all())
        sizes = list(Size.objects.all())

        for _ in range(product_count):
            vendor_profile = random.choice(vendor_profiles)
            vendor = vendor_profile.user
            category = random.choice(categories)
            subcategories = SubCategory.objects.filter(category=category)
            subcategory = random.choice(subcategories) if subcategories.exists() else None

            # Construct a realistic product name
            type_name = random.choice(self.PRODUCT_TYPES)
            product_base = subcategory.name if subcategory else "Apparel"
            product_name = f"{category.name} {type_name} {product_base}"

            product = Product.objects.create(
                vendor=vendor,
                category=category,
                subcategory=subcategory,
                fit_type=random.choice(fittypes),
                brand=random.choice(brands),
                name=product_name,
                description=fake.paragraph(),
                short_description=fake.sentence(),
                price=round(random.uniform(50, 500), 2),
                sale_price=round(random.uniform(20, 300), 2),
                stock_quantity=random.randint(0, 50),
                is_best_seller=random.choice([True, False]),
                is_new_arrival=random.choice([True, False]),
                is_featured=random.choice([True, False]),
                slug=slugify(f"{product_name}-{fake.unique.word()}")
            )

            for _ in range(random.randint(1, 3)):
                ProductImage.objects.create(
                    product=product,
                    image="products/sample.jpg"
                )

            for color in random.sample(colors, k=min(2, len(colors))):
                for size in random.sample(sizes, k=min(3, len(sizes))):
                    ProductVariant.objects.create(
                        product=product,
                        color=color,
                        size=size,
                        stock_quantity=random.randint(0, 100)
                    )

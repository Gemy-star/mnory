#!/usr/bin/env python
import os
import sys
import django

# Setup Django
sys.path.append(".")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mnory.settings.local")
django.setup()

from shop.models import Product


def check_products():
    print("=== All Products in Database ===")
    all_products = Product.objects.filter(is_active=True, is_available=True)[:20]

    print(f"Total active products: {all_products.count()}")

    for i, product in enumerate(all_products, 1):
        print(f"\n{i}. Product: {product.name}")
        print(f"   Slug: {product.slug}")
        print(
            f"   Description: {product.description[:100] if product.description else 'No description'}..."
        )

        # Check images
        images = product.images.all()
        print(f"   Images ({images.count()}):")
        for img in images:
            print(
                f"     - {img.image.name} (main: {img.is_main}, hover: {img.is_hover})"
            )

        # Check if this would be filtered out
        is_test_name = any(
            word in product.name.lower() for word in ["test", "dummy", "sample"]
        )
        is_test_desc = product.description and any(
            word in product.description.lower() for word in ["test", "dummy", "sample"]
        )
        has_sample_images = any(
            "sample.jpg" in img.image.name
            or "test.jpg" in img.image.name
            or "dummy.jpg" in img.image.name
            for img in images
        )

        would_be_filtered = is_test_name or is_test_desc or has_sample_images
        print(
            f"   Would be filtered: {would_be_filtered} (name: {is_test_name}, desc: {is_test_desc}, images: {has_sample_images})"
        )


if __name__ == "__main__":
    check_products()

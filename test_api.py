#!/usr/bin/env python
import os
import sys
import django
import requests

# Setup Django
sys.path.append(".")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mnory.settings.local")
django.setup()

from shop.models import Product


def test_api():
    try:
        # Test the API endpoint
        response = requests.get("http://127.0.0.1:8000/api/products/?category=all")
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"Number of products: {len(data.get('products', []))}")

            if data.get("products"):
                first_product = data["products"][0]
                print(f"First product: {first_product.get('name', 'N/A')}")
                print(f"Main image: {first_product.get('image', 'N/A')}")
                print(f"Hover image: {first_product.get('hover_image', 'N/A')}")
                print(
                    f"Has hover image: {'Yes' if first_product.get('hover_image') != first_product.get('image') else 'No'}"
                )
        else:
            print(f"Error: {response.text}")

    except Exception as e:
        print(f"Error testing API: {e}")


def check_products():
    print("=== Checking Products in Database ===")
    products = Product.objects.filter(is_active=True)[:5]

    for product in products:
        print(f"\nProduct: {product.name}")
        main_img = product.get_main_image()
        hover_img = product.get_hover_image()

        print(f"Main image: {main_img.image.url if main_img else 'None'}")
        print(f"Hover image: {hover_img.image.url if hover_img else 'None'}")
        print(
            f"Has separate hover: {'Yes' if hover_img and hover_img != main_img else 'No'}"
        )

        # Check all images
        images = product.images.all()
        print(f"Total images: {images.count()}")
        for img in images:
            print(f"  - {img.image.url} (main: {img.is_main}, hover: {img.is_hover})")


if __name__ == "__main__":
    check_products()
    print("\n" + "=" * 50 + "\n")
    test_api()

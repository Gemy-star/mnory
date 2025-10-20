from django.http import JsonResponse
from shop.models import Product


def simple_products_api(request):
    """Simple test API"""
    try:
        products = Product.objects.filter(is_active=True, is_available=True)[:12]

        products_data = []
        for product in products:
            products_data.append(
                {
                    "id": product.pk,
                    "name": product.name,
                    "price": str(product.price),
                }
            )

        return JsonResponse(
            {"success": True, "products": products_data, "count": len(products_data)}
        )
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})

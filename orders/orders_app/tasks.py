from orders.celery import app
from .models import Category, ProductInfo, Parameter, ProductParameter, Product, Shop
import yaml
import logging


def open_file(shop):
    with open(shop.get_file(), 'r') as f:
        data = yaml.safe_load(f)
    return data


@app.task
def save_models_from_file(shop_id):
    shop = Shop.objects.get(id=shop_id)
    file = open_file(shop)
    for cat in file['categories']:
        category, _ = Category.objects.get_or_create(id=cat['id'], name=cat['name'])
        category.shops.add(shop)
        category.save()
    for products in file['goods']:
        product, _ = Product.objects.get_or_create(id=products['id'], model=products['model'])
        try:
            product.category = Category.objects.get(id=products['category'])
        except Category.DoesNotExist:
            logging.warning(f"Не существует такой категории товаров: {products['category']}")
        product_info, _ = ProductInfo.objects.get_or_create(name=products['name'],
                                                            quantity=products['quantity'], price=products['price'],
                                                            price_rrc=products['price_rrc'])
        product_info.shop = shop
        product_info.product = product
        product_info.save()
        for params in products['parameters']:
            parameter, _ = Parameter.objects.get_or_create(name=params)
            product_parameter, _ = ProductParameter.objects.get_or_create(product_info=product_info,
                                                                          parameter=parameter,
                                                                          value=products['parameters'][params])

from django.contrib.auth.models import AbstractUser, UserManager
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.conf import settings
from django.core.files.storage import FileSystemStorage
import os

STORAGE = FileSystemStorage(location=settings.STORAGE)

USER_TYPE_CHOICES = (
    ('shop', 'Магазин'),
    ('buyer', 'Покупатель'),

)


class Shop(models.Model):
    owner = models.ForeignKey('User', related_name='shops', on_delete=models.CASCADE)
    name = models.CharField(max_length=50, unique=True)
    filename = models.FileField(storage=STORAGE)

    def __str__(self):
        return self.name

    def get_file(self):
        return os.path.join(settings.STORAGE, self.filename.name)


class Category(models.Model):
    id = models.PositiveIntegerField(unique=True, primary_key=True)
    name = models.CharField(max_length=50)
    shops = models.ManyToManyField(Shop, related_name='categories', blank=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    id = models.PositiveIntegerField(unique=True, primary_key=True)
    model = models.CharField(max_length=50)
    category = models.ForeignKey(Category, related_name='products', blank=True, null=True, on_delete=models.CASCADE)
    shops = models.ManyToManyField(Shop, through='ProductInfo', blank=True, related_name='products')

    def __str__(self):
        return self.model


class ProductInfo(models.Model):
    name = models.CharField(max_length=50)
    product = models.ForeignKey(Product, related_name='product_info_product', blank=True, null=True,
                                on_delete=models.CASCADE)
    shop = models.ForeignKey(Shop, related_name='product_info_shop', blank=True, null=True, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.PositiveIntegerField()
    price_rrc = models.PositiveIntegerField()

    parameters = models.ManyToManyField('Parameter', through='ProductParameter')


class Parameter(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return f'{self.name}'


class ProductParameter(models.Model):
    product_info = models.ForeignKey(ProductInfo, related_name='product_parameters_info', blank=True, null=True,
                                     on_delete=models.CASCADE)
    parameter = models.ForeignKey(Parameter, related_name='product_parameters_parameter', blank=True, null=True,
                                  on_delete=models.CASCADE)
    value = models.CharField(max_length=50)


class Order(models.Model):
    user = models.ForeignKey('User', related_name='orders', blank=True, null=True, on_delete=models.CASCADE)
    dt = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return str(self.dt)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='order_items', blank=True, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='order_items', blank=True, on_delete=models.CASCADE)
    shop = models.ForeignKey(Shop, related_name='order_items', blank=True, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()


class Contact(models.Model):
    type = models.CharField(max_length=50)
    user = models.ForeignKey('User', related_name='contacts', blank=True, on_delete=models.CASCADE)
    value = models.CharField(max_length=50)


class User(AbstractUser):
    REQUIRED_FIELDS = ['username']
    USERNAME_FIELD = 'email'
    email = models.EmailField(unique=True)
    username_validator = UnicodeUsernameValidator()
    username = models.CharField(max_length=150, validators=[username_validator, ])
    company = models.CharField(max_length=40, blank=True)
    position = models.CharField(max_length=40, blank=True)
    type = models.CharField(choices=USER_TYPE_CHOICES, max_length=5, default='buyer')

    def __str__(self):
        return self.email

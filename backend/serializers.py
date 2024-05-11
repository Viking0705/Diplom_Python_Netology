from rest_framework.serializers import ModelSerializer
from rest_framework import serializers

from .models import User, Shop, Category, Product, ProductInfo, Parameter, ProductParameter, Contact, Order

from djoser.compat import get_user_email, get_user_email_field_name
from djoser.conf import settings
from djoser.serializers import UserCreateSerializer, UserSerializer



class ContactSerializer(ModelSerializer):
    class Meta:
        model = Contact
        fields = ('id', 'user', 'phone', 'adress',)
        read_only_fields = ('id',)
        extra_kwargs = {
            'user': {'write_only': True},
        }

class CastomUserCreateSerializer(UserCreateSerializer):
    contacts = ContactSerializer(read_only=True, many = True)

    class Meta:
        model = User
        fields = tuple(User.REQUIRED_FIELDS) + (
            settings.LOGIN_FIELD,
            settings.USER_ID_FIELD,
            'usertype',
            'contacts',
        )

class CastomUserSerializer(UserSerializer):
    contacts = ContactSerializer(read_only=True, many = True)

    class Meta:
        model = User
        fields = tuple(User.REQUIRED_FIELDS) + (
            settings.USER_ID_FIELD,
            settings.LOGIN_FIELD,
            'usertype',
            'contacts',
        )
        read_only_fields = (settings.LOGIN_FIELD,)





class ShopSerializer(serializers.ModelSerializer):
    user = CastomUserSerializer(read_only=True)
    class Meta:
        model = Shop
        fields = ('id', 'name', 'state', 'user')
        read_only_fields = ('id',)


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name',)
        read_only_fields = ('id',)

class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)

    class Meta:
        model = Product
        fields = ('id', 'name', 'category',)

class ProductInfoSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = ProductInfo
        fields = ('id', 'product', 'model', 'quantity', 'price', 'price_rrc', 'shop',)

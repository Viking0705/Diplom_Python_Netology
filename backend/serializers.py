from rest_framework.serializers import ModelSerializer
from rest_framework import serializers

from .models import User, Shop, Category, Product, ProductInfo, Parameter, ProductParameter, Contact, Order

from djoser.conf import settings
from djoser.serializers import UserCreateSerializer, UserSerializer

from django.db.models import Q
from rest_framework.exceptions import ValidationError

class ContactSerializer(ModelSerializer):
    class Meta:
        model = Contact
        fields = ('id', 'user', 'phone', 'adress',)
        read_only_fields = ('id', ' user')

    # Обновить контакт можно только если значения обновляемых полей не достигли лимита (5 адресов, 1 телефон).
    # Если достигли, удаляем один из контактов и создаем новый
    def validate(self, data):
        request = self.context.get('request')
        phone_count = Contact.objects.filter(Q(user=request.user.id) & ~Q(phone=None)).count()
        print(phone_count)        
        adress_count = Contact.objects.filter(Q(user=request.user.id) &  ~Q(adress=None)).count()
        print(adress_count)
        if request.data.get('phone') == None and request.data.get('adress') == None:
            raise ValidationError({'error': 'Заполните телефон или адрес'})
        elif (request.data.get('phone') != None and phone_count >= 1) or (request.data.get('adress') != None and adress_count >= 5):
            raise ValidationError({'error': 'Вы можете добавить не более 1 телефона и 5 адресов'})
        else:
            return data
        

class CastomUserCreateSerializer(UserCreateSerializer):
    password = serializers.CharField(style={"input_type": "password"}, write_only=True)

    class Meta:
        model = User
        fields = tuple(User.REQUIRED_FIELDS) + (
            settings.LOGIN_FIELD,
            settings.USER_ID_FIELD,
            'usertype',
            'password',
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

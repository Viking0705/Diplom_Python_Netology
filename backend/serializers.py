from rest_framework.serializers import ModelSerializer
from rest_framework import serializers

from .models import User, Shop, Category, Product, ProductInfo, Parameter, ProductParameter, Contact, Order

from djoser.compat import get_user_email, get_user_email_field_name
from djoser.conf import settings
from djoser.serializers import UserCreateSerializer, UserSerializer

# class UserCastomSerializer(ModelSerializer):
#     class Meta:
#         model = User
#         fields = ['id', 'username', 'email', 'usertype']
#         read_only_fields = ('id',)
#         extra_kwargs = {
#             'password': {'write_only': True},
#         }
# class UserCastomSerializer(serializers.HyperlinkedModelSerializer):
#     class Meta:
#         model = User
#         fields = tuple(User.REQUIRED_FIELDS) + (
#             settings.USER_ID_FIELD,
#             settings.LOGIN_FIELD,
#             # 'usertype',
#         )
#         # fields = ['id', 'username', 'email', 'usertype']
#         read_only_fields = (settings.LOGIN_FIELD,)
    

#     def update(self, instance, validated_data):
#         email_field = get_user_email_field_name(User)
#         instance.email_changed = False
#         if settings.SEND_ACTIVATION_EMAIL and email_field in validated_data:
#             instance_email = get_user_email(instance)
#             if instance_email != validated_data[email_field]:
#                 instance.is_active = False
#                 instance.email_changed = True
#                 instance.save(update_fields=["is_active"])
#         return super().update(instance, validated_data)

#     # def to_representation(self, instance):
#     #     data = super(UserCastomSerializer, self).to_representation(instance)
#     #     data['username'] = data['username'].upper()
#     #     return data    

class ContactSerializer(ModelSerializer):
    class Meta:
        model = Contact
        fields = ('id', 'user', 'phone', 'adress',)
        read_only_fields = ('id',)
        # extra_kwargs = {
        #     'user': {'write_only': True},
        # }

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

class ShopSerializer(ModelSerializer):
    class Meta:
        model = Shop
        fields = '__all__'
        read_only_fields = ('id',)

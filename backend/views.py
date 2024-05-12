from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ViewSet
from django.db.models import Q
from django.db.models import Sum
from django.http import JsonResponse
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework import mixins

import yaml
import requests


from .models import User, Shop, Category, Product, ProductInfo, Parameter, ProductParameter, Contact, Order
from .serializers import  ContactSerializer, ShopSerializer, ProductInfoSerializer
from .permissions import IsOwner, IsOwnerOrReadOnly, IsShop, IsOwnerProdInf, IsBuyer


from django.core.validators import URLValidator

from django.conf import settings

from django.core.mail import send_mail

class ContactViewSet(ModelViewSet):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    permission_classes = [IsAuthenticated, IsOwner, IsBuyer]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        return super().perform_create(serializer)
    
        
class LoadCatalog(APIView):
    permission_classes = [IsAuthenticated, IsShop,]
    def post(self, request, *args, **kwargs):
        url = request.data.get('url')
        if url:
            content = requests.get(url).content.decode('utf-8')
            data = yaml.load(content, Loader=yaml.Loader)

            get_shop_name = data.get('shop')    
            if get_shop_name:
                print(data.get('shop'))
                shop, created = Shop.objects.get_or_create(name=get_shop_name,
                                                           url = url,
                                                           state = True,
                                                           user_id = request.user.id)
                print(shop.id)

                for cat in data.get('categories'):
                    category, created= Category.objects.get_or_create(id=cat.get('id'), name=cat.get('name'))
                    print(created)
                    category.shops.add(shop.id)
                    category.save()

                for good in data.get('goods'):
                    product, created = Product.objects.get_or_create(id=good.get('id'),
                                                                     name=good.get('name'),
                                                                     category_id=good.get('category'))
                    prod_inf, created = ProductInfo.objects.get_or_create(model=good.get('model'), 
                                                                      price=good.get('price'),
                                                                      price_rrc=good.get('price_rrc'),
                                                                      quantity=good.get('quantity'),
                                                                      shop_id=shop.id,
                                                                      product_id=product.id)
                    
                    for param, val in good.get('parameters').items():
                        parameter, created = Parameter.objects.get_or_create(name=param)
                        product_parameter, created = ProductParameter.objects.get_or_create(product_info_id=prod_inf.id,
                                                                                            parameter_id=parameter.id,
                                                                                            value=val)

            return Response(data)

class ShopViewSet(ModelViewSet):
    queryset = Shop.objects.all()
    serializer_class = ShopSerializer
    # permission_classes = [IsAuthenticated, IsOwnerOrReadOnly,]

    # def get_queryset(self):
    #     return Shop.objects.all().filter(state=True)

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = []
        else:
            permission_classes = [IsAuthenticated, IsShop, IsOwner]
        return [permission() for permission in permission_classes]

class ProductInfoViewSet(ModelViewSet):
    # queryset = ProductInfo.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['shop', 'product__category', ]
    serializer_class = ProductInfoSerializer

    def get_queryset(self):
        return ProductInfo.objects.filter(shop__state=True)

    def get_permissions(self):
        print(self.action)
        if self.action in ['list', 'retrieve']:
            permission_classes = []
        else:
            permission_classes = [IsAuthenticated, IsShop, IsOwnerProdInf]
        return [permission() for permission in permission_classes]
    

class BasketViewSet(ModelViewSet):
    queryset = Order.objects.all()
    permission_classes = [IsAuthenticated, IsBuyer, IsOwner]

    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
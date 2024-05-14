from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ViewSet
from django.db.models import Q, F, Sum
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


from .models import User, Shop, Category, Product, ProductInfo, Parameter, ProductParameter, Contact, Order, OrderItem
from .serializers import  ContactSerializer, ShopSerializer, ProductInfoSerializer, OrderSerializer
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
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated, IsBuyer, IsOwner]

    def get_queryset(self):
        data = Order.objects.filter(user = self.request.user.id, state = 'basket')\
        .annotate(total_sum=Sum(F('ordered_items__product_info__price') * F('ordered_items__quantity')))
        print(data)
        return data
    
    def create(self, request, *args, **kwargs):
        product_info_id = request.data.get('product_info_id')
        wish_quantity = int(request.data.get('quantity'))      

        if ProductInfo.objects.filter(id=product_info_id).exists():
            stock_quantity = ProductInfo.objects.get(id=product_info_id).quantity
            quantity = (stock_quantity if stock_quantity < wish_quantity else wish_quantity)
            basket, created = Order.objects.get_or_create(state='basket', user_id=self.request.user.id)

            if OrderItem.objects.filter(product_info_id=product_info_id).exists():
                raise ValidationError('Такой товар уже есть в корзине')
            else:
                item, created = OrderItem.objects.get_or_create(order_id=basket.id,
                                                                quantity=quantity,
                                                                product_info_id=product_info_id)
                return Response(status=status.HTTP_201_CREATED)
        else:
   
            raise ValidationError('Такого товара нет в каталоге')

    
    def update(self, request, *args, **kwargs):
        product_info_id = self.kwargs.get('pk')
        wish_quantity = int(request.data.get('quantity'))

        product_info_id_in_basket = list(OrderItem.objects.values_list("product_info_id", flat=True))
        if int(product_info_id) in product_info_id_in_basket:
            stock_quantity = ProductInfo.objects.get(id=product_info_id).quantity
            quantity = (stock_quantity if stock_quantity < wish_quantity  else wish_quantity)
            item = OrderItem.objects.filter(product_info_id=product_info_id).update(quantity=quantity)
        else:    
            raise ValidationError("Такого товара нет в корзине")

        return Response(status=status.HTTP_200_OK)
    
    def delete(self, request, *args, **kwargs):
        product_info_id = request.data.get('product_info_id')
        # order_id = self.kwargs.get('pk')
        # print(int(product_info_id))
        # print(int(order_id))

        # удаление товара из корзины
        if int(product_info_id)>0:
            print(product_info_id)
            item = OrderItem.objects.filter(product_info_id=product_info_id).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        
        # удаление корзины по id заказа (очистка корзины):
        order_id = self.kwargs.get('pk')
        if int(order_id)>0:
            print('Удаляем')
            item = Order.objects.filter(id=order_id).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            print('Корзины нет')
            return False
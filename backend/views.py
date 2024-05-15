from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from django.db.models import F, Sum
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from django.conf import settings
from django.core.mail import send_mail

import yaml
import requests

from .models import User, Shop, Category, Product, ProductInfo, Parameter, ProductParameter, Contact, Order, OrderItem, STATE_CHOICES
from .serializers import  ContactSerializer, ShopSerializer, ProductInfoSerializer, OrderSerializer
from .permissions import IsOwner, IsShop, IsOwnerProdInf, IsBuyer

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
                shop, created = Shop.objects.get_or_create(name=get_shop_name,
                                                           url = url,
                                                           state = True,
                                                           user_id = request.user.id)

                for cat in data.get('categories'):
                    category, created= Category.objects.get_or_create(id=cat.get('id'), name=cat.get('name'))
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

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = []
        else:
            permission_classes = [IsAuthenticated, IsShop, IsOwner]
        return [permission() for permission in permission_classes]

class ProductInfoViewSet(ModelViewSet):
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['shop', 'product__category', ]
    serializer_class = ProductInfoSerializer

    def get_queryset(self):
        return ProductInfo.objects.filter(shop__state=True)

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = []
        else:
            permission_classes = [IsAuthenticated, IsShop, IsOwnerProdInf]
        return [permission() for permission in permission_classes]
    

class BasketViewSet(ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated, IsBuyer, IsOwner]

    def get_queryset(self):
        data = Order.objects.filter(user = self.request.user.id, state = 'basket')\
        .annotate(total_sum=Sum(F('ordered_items__product_info__price') * F('ordered_items__quantity')))
        if not data:
            return Response(status=status.HTTP_404_NOT_FOUND, data={'error': 'Заказов в корзине нет'})    
        return data
    
    def create(self, request, *args, **kwargs):
        product_info_id = request.data.get('product_info_id')
        wish_quantity = int(request.data.get('quantity'))      

        if ProductInfo.objects.filter(id=product_info_id).exists():
            stock_quantity = ProductInfo.objects.get(id=product_info_id).quantity
            quantity = (stock_quantity if stock_quantity < wish_quantity else wish_quantity)
            basket, created = Order.objects.get_or_create(state='basket', user_id=self.request.user.id)

            if OrderItem.objects.filter(product_info_id=product_info_id, order_id__state='basket').exists():
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

        # удаление товара из корзины
        if int(product_info_id) > 0:
            item = OrderItem.objects.filter(product_info_id=product_info_id).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        
        # удаление корзины по id заказа (очистка корзины):
        order_id = self.kwargs.get('pk')
        if int(order_id) > 0:
            item = Order.objects.filter(id=order_id).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return False


class OrderViewSet(ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated, IsBuyer, IsOwner]

    def get_queryset(self):
        data = Order.objects.filter(user = self.request.user.id, state__in=list(list(zip(*STATE_CHOICES))[0]))\
        .annotate(total_sum=Sum(F('ordered_items__product_info__price') * F('ordered_items__quantity')))
        return data
    
    def create(self, request, *args, **kwargs):

        if request.data.get('contact_id') == None:
            raise ValidationError('Для оформления заказа нужны контакты покупателя')

        for q in OrderItem.objects.filter(order__state='basket').values_list("product_info_id", "quantity"):
            if q[1] > ProductInfo.objects.get(id=q[0]).quantity:
                raise ValidationError('На складе недостаточно товара')
            else:
                ProductInfo.objects.filter(id=q[0]).update(quantity= F('quantity') - q[1])

        new_order = Order.objects.get(user_id = request.user.id,
                                    state ='basket').id
        Order.objects.filter(user_id = request.user.id,
                                           state ='basket').update(state='new', contact_id = request.data.get('contact_id'))
 
        send_mail('New order My_shop',
                  f"Вы оформили новый заказ № {new_order}.", 
                  settings.DEFAULT_FROM_EMAIL,
                  [request.user.email], fail_silently=False)

        shop_email_in_order = OrderItem.objects.filter(order=new_order).values_list('product_info__shop_id__user__email', flat=True).distinct()
        send_mail('Новый заказ My_shop',
                  f"Магазин получил новый заказ № {new_order}.", 
                  settings.DEFAULT_FROM_EMAIL,
                  shop_email_in_order, fail_silently=False)
        return Response(status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        order_id= self.kwargs.get('pk')
        order_state = Order.objects.get(id=order_id).state

        Order.objects.filter(id=order_id).update(state='canceled')

        if order_state in ['new', 'preparation']:
            buyer_id = Order.objects.get(id=order_id).user_id
            buyer_email = User.objects.get(id=buyer_id).email
            send_mail('Отмена заказ My_shop',
                  f"Вы отменили заказ № {order_id}.", 
                  settings.DEFAULT_FROM_EMAIL,
                  [buyer_email], fail_silently=False)
            for q in OrderItem.objects.filter(order_id=order_id).values_list('product_info_id', 'quantity'):
                ProductInfo.objects.filter(id=q[0]).update(quantity= F('quantity') + q[1])            
        return Response(status=status.HTTP_200_OK)


class OrderShopViewSet(ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated, IsShop]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['state', ]

    def get_queryset(self):
        data= Order.objects.filter(ordered_items__product_info__shop__user_id = self.request.user.id, 
                                   state__in=['new', 'preparation', 'sent', 'deliverd', 'completed', 'canceled'])\
            .annotate(total_sum=Sum(F('ordered_items__product_info__price') * F('ordered_items__quantity')))
        return data
    
    def update(self, request, *args, **kwargs):
        upd_state_dict = {
            'new': 'preparation',
            'preparation':'sent',
            'sent': 'delivered',
            'delivered': 'completed',            
        }

        order_id= self.kwargs.get('pk')
        if int(order_id) not in Order.objects.all().values_list('id', flat=True):
            raise ValidationError('Такого заказа нет')

        current_state = Order.objects.get(id=order_id).state
        if current_state in upd_state_dict:
            upd_state = upd_state_dict.get(current_state)
            Order.objects.filter(id=order_id).update(state=upd_state)
            buyer_email = Order.objects.filter(id=order_id).values_list('user_id__email', flat=True).distinct()
            send_mail('Изменение статуса заказа My_shop',
                  f"Ваш заказ № {order_id} изменил статус на: \"{dict(STATE_CHOICES)[upd_state]}\".",
                  settings.DEFAULT_FROM_EMAIL,
                  list(buyer_email), fail_silently=False)
        else:
            raise ValidationError('Статус заказа не может быть изменен')            
        return Response(status=status.HTTP_200_OK)
    
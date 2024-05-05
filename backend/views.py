from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from django.db.models import Q
from django.http import JsonResponse

from rest_framework.generics import GenericAPIView

from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .models import User, Shop, Category, Product, ProductInfo, Parameter, ProductParameter, Contact, Order
from .serializers import  ContactSerializer


from django.core.validators import URLValidator

class ContactViewSet(ModelViewSet):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    permission_classes = (IsAuthenticated,)
    
    def create(self, request, *args, **kwargs):
        phone_count = Contact.objects.filter(Q(user=request.user) & ~Q(phone='')).count()
        adress_count = Contact.objects.filter(Q(user=request.user) & ~Q(adress='')).count()
        if request.data.get('phone') == '' and request.data.get('adress') == '':
            return Response({'error': 'Заполните телефон или адрес'}, status=status.HTTP_400_BAD_REQUEST)
        elif (request.data.get('phone') != '' and phone_count >= 6) or (request.data.get('adress') != '' and adress_count >= 10):
            return Response({'error': 'Вы можете добавить не более 6 телефонов и 10 адресов'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return super().create(request, *args, **kwargs)


# class ShopViewSet(ModelViewSet):
#     queryset = Shop.objects.all()
#     serializer_class = ShopSerializer
#     permission_classes = (IsAuthenticated,)

#     def get_queryset(self):
#         return Shop.objects.filter(user=self.request.user)
    

from rest_framework.permissions import BasePermission

from .models import Shop

class IsOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user.id == obj.user_id

class IsOwnerOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method == 'GET':
            return True
        return request.user.id == obj.user_id
    
class IsShop(BasePermission):
    def has_permission(self, request, view):
        if request.user.usertype =='shop': # or request.user.is_superuser:
            return True
        else:
            return False
        
    # def has_object_permission(self, request, view, obj):
    #         return request.user.id == obj.user_id

class IsOwnerProdInf(BasePermission):
    def has_object_permission(self, request, view, obj):
        shop = Shop.objects.get(user=request.user.id)
        print(shop.id)
        print(obj.shop_id)
        return shop.id == obj.shop_id
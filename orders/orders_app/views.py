from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import ValidationError
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import ShopSerializer, ProductSerializer, UserSerializer, OrderItemSerializer
from .models import Shop, Product, User, Order, OrderItem
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from orders_app.permissions import IsShop, IsOwnerOrReadOnly, IsOwnerOfProfile
from rest_framework import mixins
from rest_framework import generics
from .tasks import save_models_from_file
from rest_framework import viewsets


class ShopView(mixins.RetrieveModelMixin,
               mixins.CreateModelMixin,
               mixins.UpdateModelMixin,
               mixins.DestroyModelMixin,
               generics.GenericAPIView, ):
    def get_permissions(self):
        if self.request.method == 'POST':
            self.permission_classes = [IsAuthenticated, IsShop]
        elif self.request.method == 'PUT':
            self.permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
        elif self.request.method == 'DELETE':
            self.permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

        return super(ShopView, self).get_permissions()

    serializer_class = ShopSerializer
    queryset = Shop.objects.all()

    def post(self, *args, **kwargs):
        return self.create(*args, **kwargs)

    def perform_create(self, serializer):
        shop = serializer.save(owner=self.request.user)
        print(self.request.user)
        print(shop.owner)
        save_models_from_file.delay(shop.id)

    def put(self, *args, **kwargs):
        return self.update(*args, **kwargs)

    def get(self, *args, **kwargs):
        return self.retrieve(*args, **kwargs)


class LoginView(APIView):
    def post(self, request):
        user = authenticate(username=request.data.get('email', None), password=request.data.get('password', None))
        if user:
            token, _ = Token.objects.get_or_create(user=user)
            return Response({'token': token.key}, status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_403_FORBIDDEN)


class AccountView(APIView):
    def get_permissions(self):
        if self.request.method == 'PUT':
            self.permission_classes = [IsAuthenticated, IsOwnerOfProfile]
        if self.request.method == 'GET':
            self.permission_classes = [IsAuthenticated, IsOwnerOfProfile]
        return super(AccountView, self).get_permissions()

    def post(self, request, *args, **kwargs):
        user_serializer = UserSerializer(data=request.data)
        if user_serializer.is_valid():
            try:
                validate_password(request.data.get('password', ''))
            except ValidationError as e:
                return Response({i: _ for i, _ in enumerate(e.messages, start=1)}, status=status.HTTP_400_BAD_REQUEST)
            user = user_serializer.save()
            user.set_password(user_serializer.validated_data['password'])
            user.save()
            return Response(status=status.HTTP_200_OK)
        else:
            return Response({'detail': user_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, *args, **kwargs):
        user = User.objects.get(id=self.request.user.id)
        user_serializer = UserSerializer(user, data=self.request.data)
        if user_serializer.is_valid():
            user = user_serializer.save()
            return Response(status=status.HTTP_200_OK)
        else:
            return Response({'detail': user_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def get(self, *args, **kwargs):
        user = User.objects.get(id=self.request.user.id)
        return Response(UserSerializer(user).data)


class ProductList(generics.ListCreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class ProductDetail(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


def get_my_order(request, *args, **kwargs):
    order, _ = Order.objects.get_or_create(user=request.user)
    return order


def get_or_None(obj, param):
    try:
        result = obj.objects.get(id=param)
    except obj.DoesNotExist:
        result = None
    return result


class OrderView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, *args, **kwargs):
        if self.request.user.type == 'buyer':
            my_order = get_my_order(request=self.request)
            queryset = OrderItem.objects.filter(order=my_order)
            return Response(OrderItemSerializer(queryset, many=True).data)
        elif self.request.user.type == 'shop':
            orders = OrderItem.objects.filter(shop=self.request.user.shops.all()[0])
            return Response(OrderItemSerializer(orders, many=True).data)

    def post(self, *args, **kwargs):
        try:
            order_item = OrderItem.objects.filter(
                shop=Shop.objects.get(id=self.request.data.get('shop', None)),
                product=Product.objects.get(id=self.request.data.get('product', None)),
                order=get_my_order(self.request),
            )
        except ObjectDoesNotExist:
            return Response('Не найден такой магазин/товар')
        if order_item.count() != 0:
            item = order_item.first()
            item.quantity = item.quantity + int(self.request.data.get('quantity'))
            item.save()
            return Response(OrderItemSerializer(item).data)
        else:
            order_item_serializer = OrderItemSerializer(data=self.request.data)
            if order_item_serializer.is_valid():
                item = order_item_serializer.save()
                return Response(OrderItemSerializer(item).data)
            else:
                return Response(order_item_serializer.errors)

    def put(self, *args, **kwargs):
        try:
            order_item = OrderItem.objects.filter(
                shop=Shop.objects.get(id=self.request.data.get('shop', None)),
                product=Product.objects.get(id=self.request.data.get('product', None)),
                order=get_my_order(self.request),
            )
        except ObjectDoesNotExist:
            return Response('Не найден такой магазин/товар')
        if order_item.count() != 0:
            item = order_item.first()
            item_serializer = OrderItemSerializer(item, data=self.request.data)
            if item_serializer.is_valid():
                result = item_serializer.save()
            return Response(OrderItemSerializer(result).data)
        else:
            return Response({'detail': 'Не найден такой элемент заказа'})

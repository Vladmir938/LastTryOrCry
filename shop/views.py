from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.db.models import Sum
from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .forms import LoginForm, AddToCartForm
from .models import Category, Product, Cart, Order, CartItem
from .serializers import CategorySerializer, ProductSerializer, CartSerializer, OrderSerializer, CartDetailSerializer
from .permissions import ManagerOrReadOnly


class CategoryApiView(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [ManagerOrReadOnly]


class ProductApiView(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [ManagerOrReadOnly]

    @action(detail=False, methods=['get'])
    def by_category(self, request):
        category_name = request.query_params.get('category')
        if not category_name:
            return Response({'error': 'Category parameter is required.'}, status=status.HTTP_400_BAD_REQUEST)
        queryset = self.get_queryset().filter(category__name=category_name)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class CartApiView(LoginRequiredMixin, viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = CartSerializer

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)


class AddToCartView(LoginRequiredMixin, APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        product_name = request.data.get('product_name')
        quantity = request.data.get('quantity')
        if not all([product_name, quantity]):
            return Response({'error': 'Both product name and quantity are required.'},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            product = Product.objects.get(name=product_name)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found.'}, status=status.HTTP_400_BAD_REQUEST)

        cart_items = []
        cart = Cart.objects.filter(user=request.user).first()
        if not cart:
            cart = Cart.objects.create(user=request.user)

        try:
            cart_item = CartItem.objects.get(product=product, cart=cart)
            cart_item.quantity += int(quantity)
            cart_item.save()
        except CartItem.DoesNotExist:
            cart_item = CartItem.objects.create(cart=cart, product=product, quantity=int(quantity))

        for item in cart.cart_items.all():
            product_data = {
                "product": CartDetailSerializer(item).data['product'],
                "quantity": item.quantity
            }
            cart_items.append(product_data)

        cart_data = {
            "id": cart.id,
            "user": cart.user.id,
            "cart_items": cart_items
        }
        serializer = CartSerializer(cart)
        return Response(serializer.data)

    def get(self, request):
        form = AddToCartForm()
        products = Product.objects.all()
        context = {'form': form, 'products': products}
        return render(request, 'add_to_cart.html', context)


class OrderApiView(LoginRequiredMixin, viewsets.ModelViewSet):
    serializer_class = OrderSerializer

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    @action(detail=True, methods=['delete'])
    def delete_order(self, request, pk=None):
        try:
            order = Order.objects.get(pk=pk)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)

        order.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
    def order_summary(self, request):
        user = request.user
        orders = Order.objects.filter(user=user)
        order_count = orders.count()
        total_price = orders.aggregate(Sum('total_price'))['total_price__sum'] or 0
        return Response({'order_count': order_count, 'total_price': total_price})


class OrderCreateApiView(LoginRequiredMixin, APIView):
    serializer_class = OrderSerializer

    def post(self, request, *args, **kwargs):
        data = request.data.copy()
        data['user'] = request.user.id
        serializer = self.serializer_class(data=data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLoginView(LoginView):
    form_class = LoginForm
    template_name = 'login.html'

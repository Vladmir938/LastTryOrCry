from rest_framework import serializers

from .models import Category, Product, CartItem, Cart, OrderItem, Order


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('name',)


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.ReadOnlyField(source='category.name')

    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'category', 'category_name', 'image']


class CartDetailSerializer(serializers.ModelSerializer):
    product = ProductSerializer()

    class Meta:
        model = CartItem
        fields = ['product', 'quantity']


class CartSerializer(serializers.ModelSerializer):
    cart_items = CartDetailSerializer(many=True, read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'user', 'cart_items']

    def create(self, validated_data):
        cart_items_data = validated_data.pop('cart_items')
        cart = Cart.objects.create(**validated_data)
        for cart_item_data in cart_items_data:
            product_data = cart_item_data.pop('product')
            product = Product.objects.get(pk=product_data['id'])
            CartItem.objects.create(cart=cart, product=product, **cart_item_data)
        return cart


class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer()

    class Meta:
        model = OrderItem
        fields = ('product', 'quantity', 'price')


class OrderSerializer(serializers.ModelSerializer):
    order_items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ('id', 'user', 'phone_number', 'delivery_address', 'total_price', 'order_items')

    def create(self, validated_data):
        user = self.context['request'].user
        carts = Cart.objects.filter(user=user)

        if carts.count() != 1:
            raise serializers.ValidationError('Должна быть одна корзина.')

        cart = carts.first()
        cart_items = cart.cart_items.all()

        total_price = 0
        for cart_item in cart_items:
            total_price += cart_item.get_total_price()

        order = Order.objects.create(user=user,
                                     total_price=total_price,
                                     phone_number=validated_data['phone_number'],
                                     delivery_address=validated_data['delivery_address'])

        for cart_item in cart_items:
            OrderItem.objects.create(order=order,
                                      product=cart_item.product,
                                      quantity=cart_item.quantity,
                                      price=cart_item.get_total_price())

        cart_items.delete()

        return order
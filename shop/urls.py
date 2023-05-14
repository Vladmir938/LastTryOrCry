from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from rest_framework import routers

from shop.views import CategoryApiView, ProductApiView, CartApiView, OrderApiView, AddToCartView, \
    OrderCreateApiView

router = routers.SimpleRouter()
router.register(r'categories', CategoryApiView, basename='categories')
router.register(r'products', ProductApiView, basename='products')
router.register(r'cart', CartApiView, basename='cart')
router.register('orders', OrderApiView, basename='orders')

urlpatterns = [
    path('', include(router.urls)),
    path('add-to-cart/', AddToCartView.as_view(), name='add_to_cart'),
    path('orders/', OrderApiView.as_view({'get': 'list'}), name='order-list'),
    path('orders/<int:pk>/', OrderApiView.as_view({'get': 'retrieve'}), name='order-detail'),
    path('orders/create/', OrderCreateApiView.as_view(), name='create_order'),
]


urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
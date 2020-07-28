from django.urls import path
from store.views import (
    home,
    product_page,
    cart_detail,
    add_cart,
    cart_remove,
    cart_remove_product,
    thanks_page,
    signup_view,
    signin_view,
    profile_view,
    search,
    logout_view,
    order_history,
    view_order,
    contact,
)


urlpatterns = [
    path('', view=home, name='home'),
    path('category/<slug:category_slug>', view=home, name='products_by_category'),
    path('category/<slug:category_slug>/<slug:product_slug>', view=product_page, name='product_detail'),
    path('cart/add/<int:product_id>', view=add_cart, name='add_cart'),
    path('cart/', view=cart_detail, name='cart_detail'),
    path('cart/remove/<int:product_id>', view=cart_remove, name='cart_remove'),
    path('cart/remove_product/<int:product_id>', view=cart_remove_product, name='cart_remove_product'),
    path('thankyou/<int:order_id>', view=thanks_page, name='thanks_page'),
    path('account/create/', view=signup_view, name='signup_view'),
    path('account/login/', view=signin_view, name='signin_view'),
    path('account/profile/', view=profile_view, name='profile_view'),
    path('account/logout/', view=logout_view, name='logout'),
    path('search/', view=search, name='search'),
    path('order_history/', view=order_history, name='order_history'),
    path('order_details/', view=order_history, name='order_history'),
    path('order/<int:order_id>', view=view_order, name='order_detail'),
    path('contact/', view=contact, name='contact'),
]


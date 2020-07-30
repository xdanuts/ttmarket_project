from django.shortcuts import render, get_object_or_404, redirect, reverse
from store.models import Category, Product, Cart, CartItem, Order, OrderItem, MyUser, Review
from django.http import HttpResponseRedirect
from django.core.exceptions import ObjectDoesNotExist
import stripe
from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.auth import login, authenticate, logout
from store.forms import LoginForm, MyUserCreationForm, ContactForm, DeliveryForm
from django.contrib.auth.decorators import login_required
from django.template.loader import get_template
from django.core.mail import EmailMessage

# Create your views here.


def home(request, category_slug=None):
    category_page = None
    products = None
    if category_slug != None:
        category_page = get_object_or_404(Category, slug=category_slug)
        products = Product.objects.filter(category=category_page, available=True)
    else:
        products = Product.objects.all().filter(available=True)
    return render(request, 'home.html', {'category': category_page, 'products': products})


def product_page(request, category_slug, product_slug):
    try:
        product = Product.objects.get(category__slug=category_slug, slug=product_slug)
    except Exception as e:
        raise e

    if request.method == 'POST' and request.user.is_authenticated and request.POST['content'].strip() != '':
        Review.objects.create(
                                product=product,
                                user=request.user,
                                content=request.POST['content']
        )

    reviews = Review.objects.filter(product=product)

    return render(request, 'product.html', {'product': product, 'reviews': reviews})


def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart


def add_cart(request, product_id):
    product = Product.objects.get(id=product_id)
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
    except Cart.DoesNotExist:
        cart = Cart.objects.create(
            cart_id=_cart_id(request)
        )
        cart.save()
    try:
        cart_item = CartItem.objects.get(product=product, cart=cart)
        if cart_item.quantity < cart_item.product.stock:
            cart_item.quantity +=1
        cart_item.save()
    except CartItem.DoesNotExist:
        cart_item = CartItem.objects.create(
            product=product,
            quantity=1,
            cart=cart
        )
        cart_item.save()

    return redirect('cart_detail')


def cart_detail(request, total=0, counter=0, cart_items=None):
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_items = CartItem.objects.filter(cart=cart, active=True)
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            counter += cart_item.quantity

    except ObjectDoesNotExist:
        pass

    stripe.api_key = settings.STRIPE_SECRET_KEY
    stripe_total = int(total * 100)
    description = 'TTMarket - New Order'
    data_key = settings.STRIPE_PUBLISHABLE_KEY
    if request.method == 'POST':
        try:
            token = request.POST['stripeToken']
            email = request.POST['stripeEmail']
            billingName = request.POST['stripeBillingName']
            billingAddress1 = request.POST['stripeBillingAddressLine1']
            billingCity = request.POST['stripeBillingAddressCity']
            billingPostcode = request.POST['stripeBillingAddressZip']
            billingCountry = request.POST['stripeBillingAddressCountryCode']
            shippingName = request.POST['stripeShippingName']
            shippingAddress1 = request.POST['stripeShippingAddressLine1']
            shippingCity = request.POST['stripeShippingAddressCity']
            shippingPostcode = request.POST['stripeShippingAddressZip']
            shippingCountry = request.POST['stripeShippingAddressCountryCode']
            customer = stripe.Customer.create(
                email=email,
                source=token
            )
            charge = stripe.Charge.create(
                amount=stripe_total,
                currency='ron',
                description=description,
                customer=customer.id
            )
            try:
                order_details = Order.objects.create(
                    token=token,
                    total=total,
                    emailAddress=email,
                    billingName=billingName,
                    billingAddress1=billingAddress1,
                    billingCity=billingCity,
                    billingPostcode=billingPostcode,
                    billingCountry=billingCountry,
                    shippingName=shippingName,
                    shippingAddress1=shippingAddress1,
                    shippingCity=shippingCity,
                    shippingPostcode=shippingPostcode,
                    shippingCountry=shippingCountry
                )
                order_details.save()
                for order_item in cart_items:
                    or_item = OrderItem.objects.create(
                        product=order_item.product.name,
                        quantity=order_item.quantity,
                        price=order_item.product.price,
                        order=order_details
                    )
                    or_item.save()

                    products = Product.objects.get(id=order_item.product.id)
                    products.stock = int(order_item.product.stock - order_item.quantity)
                    products.save()
                    order_item.delete()

                    print('The order has been created!')
                try:
                    send_email(order_details.id)
                    print('The order email has been sent.')
                except IOError as e:
                    return e

                return redirect('thanks_page', order_details.id)
            except ObjectDoesNotExist:
                pass

        except stripe.error.CardError as e:
            return False, e

    return render(request, 'cart.html', dict(
        cart_items=cart_items,
        total=total,
        counter=counter,
        data_key=data_key,
        stripe_total=stripe_total,
        description=description
    ))


def cart_remove(request, product_id):
    cart = Cart.objects.get(cart_id=_cart_id(request))
    product = get_object_or_404(Product, id=product_id)
    cart_item = CartItem.objects.get(product=product, cart=cart)
    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save()
    else:
        cart_item.delete()
    return redirect('cart_detail')


def cart_remove_product(request, product_id):
    cart = Cart.objects.get(cart_id=_cart_id(request))
    product = get_object_or_404(Product, id=product_id)
    cart_item = CartItem.objects.get(product=product, cart=cart)
    cart_item.delete()
    return redirect('cart_detail')


def thanks_page(request, order_id):
    if order_id:
        customer_order = get_object_or_404(Order, id=order_id)
    return render(request, 'thankyou.html', {'customer_order': customer_order})


def signup_view(request):
    if request.method == 'POST':
        form = MyUserCreationForm(request.POST)

        if form.is_valid():
            form.save()
    else:
        form = MyUserCreationForm()

    return render(request, 'signup.html', {'form': form})


def signin_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)

        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(request, username=email, password=password)

            if user is not None:
                login(request, user)
                # return HttpResponseRedirect(reverse('profile_view'))
                return redirect('home')
            else:
                return redirect('signup_view')

    else:
        form = LoginForm()

    return render(request, 'login.html', {'form': form})


def profile_view(request):
    return render(request, 'profile.html')


def search(request):
    products = Product.objects.filter(name__icontains=request.GET['title'])
    return render(request, 'home.html', {'products': products})


def logout_view(request):
    logout(request)
    return redirect('signin_view')


@login_required(redirect_field_name='next', login_url='signin_view')
def order_history(request):
    if request.user.is_authenticated:
        email = str(request.user.email)
        order_details = Order.objects.filter(emailAddress=email)

    return render(request, 'orders_list.html', {'order_details': order_details})


@login_required(redirect_field_name='next', login_url='signin_view')
def view_order(request, order_id):
    if request.user.is_authenticated:
        email = str(request.user.email)
        order = Order.objects.get(id=order_id, emailAddress=email)
        order_items = OrderItem.objects.filter(order=order)
    return render(request, 'order_detail.html', {'order': order, 'order_items': order_items})


def send_email(order_id):
    transaction = Order.objects.get(id=order_id)
    order_items = OrderItem.objects.filter(order=transaction)

    try:
        subject = 'TTMarket - New Order #{}'.format(transaction.id)
        to = ['{}'.format(transaction.emailAddress)]
        from_email = 'danutsxd@gmail.com'
        order_information = {
            'transaction': transaction,
            'order_items': order_items,
        }
        message = get_template('email/email.html').render(order_information)
        msg = EmailMessage(subject, message, to=to, from_email=from_email)
        msg.content_subtype = 'html'
        msg.send()
    except IOError as e:
        return e


def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            subject = form.cleaned_data.get('subject')
            from_email = form.cleaned_data.get('from_email')
            message = form.cleaned_data.get('message')
            name = form.cleaned_data.get('name')

            message_format = '{0} with e-mail address "{1}" has sent you a new message:\n\n{2}'.format(
                name,
                from_email,
                message
            )

            msg = EmailMessage(
                       subject,
                       message_format,
                       to=[settings.EMAIL_HOST_USER],
                       from_email=from_email
            )

            msg.send()

            return render(request, 'contact_success.html')

    else:
        form = ContactForm()

    return render(request, 'contact.html', {'form': form})


def about(request):
    return render(request, 'about.html')


def on_delivery(request, total=0):
    cart = Cart.objects.get(cart_id=_cart_id(request))
    cart_items = CartItem.objects.filter(cart=cart, active=True)
    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
        names = cart_item.product.name
        quantities = cart_item.quantity

    if request.method == 'POST':
        form = DeliveryForm(request.POST)
        if form.is_valid():
            emailAddress = form.cleaned_data.get('emailAddress')
            shippingName = form.cleaned_data.get('shippingName')
            shippingAddress1 = form.cleaned_data.get('shippingAddress1')
            shippingCity = form.cleaned_data.get('shippingCity')
            shippingPostcode = form.cleaned_data.get('shippingPostcode')
            shippingCountry = form.cleaned_data.get('shippingCountry')
            phone_number = form.cleaned_data.get('phone_number')

            subject = "A new order has been placed."
            message_format = "{0} placed an order! Check details below:\n\n" \
                             "Name: {1}\n" \
                             "City: {2}\n" \
                             "Zip Code: {3}\n" \
                             "Country: {4}\n" \
                             "Phone Number: {5}" \
                             "\n\nReceived from {6}." \
                             "\n\nCart details:\n{7}" \
                             "\nQuantity: {8}".format(

                shippingName,
                shippingAddress1,
                shippingCity,
                shippingPostcode,
                shippingCountry,
                phone_number,
                emailAddress,
                names,
                quantities
            )

            msg = EmailMessage(
                    subject,
                    message_format,
                    to=[settings.EMAIL_HOST_USER],
                    from_email=emailAddress
                )

            msg.send()

            return render(request, 'delivery_success.html')

    else:
        form = DeliveryForm()

    return render(request, 'on_delivery.html', {'form': form, 'cart_items': cart_items, 'total': total})

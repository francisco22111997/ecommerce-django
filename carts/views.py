
from django.shortcuts import get_object_or_404, render, redirect
from store.models import Product, Variation
from .models import Cart, CartItem
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required

# Create your views here.

# Funcion privada


def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart


# creacion del carrito de compras
def add_cart(request, product_id):
    product = Product.objects.get(id=product_id)

    #Obtener el user en sesion
    current_user = request.user

    if current_user.is_authenticated:
        # aqui agregamos la logica del carrito de compras cuando
        # el usuario esta autenticado
        product_variation = []

        if request.method == 'POST':
            for item in request.POST:
                key = item
                value = request.POST[key]

                try:
                    variation = Variation.objects.get(
                        product=product, variation_category__iexact=key, variation_value__ixact=value)
                    product_variation.append(variation)
                except:
                    pass

        is_cart_item_exists = CartItem.objects.filter(
            product=product, user=current_user).exists()
        # Insercion del record
        if is_cart_item_exists:
            cart_item = CartItem.objects.filter(product=product, user=current_user)
            # capturar los variations que vienen desde la base de datos

            ex_var_list = []
            id = []
            for item in cart_item:
                existing_variation = item.variations.all()
                ex_var_list.append(list(existing_variation))
                id.append(item.id)

            if product_variation in ex_var_list:
                index = ex_var_list.index(product_variation)
                item_id = id[index]
                item = CartItem.objects.get(product=product, id=item_id)
                item.quantity += 1
                item.save()
            else:
                item = CartItem.objects.create(
                    product=product, quantity=1, user=current_user)
                # Insertar cada variation al cartItem
                if len(product_variation) > 0:
                    item.variations.clear()
                    item.variations.add(*product_variation)
                item.save()

        else:
            cart_item = CartItem.objects.create(
                product=product,
                quantity=1,
                user=current_user,
            )
            if len(product_variation) > 0:
                cart_item.variations.clear()
                cart_item.variations.add(*product_variation)
            cart_item.save()
        
        return redirect('cart')       
    else:

        product_variation = []

        if request.method == 'POST':
            for item in request.POST:
                key = item
                value = request.POST[key]

                try:
                    variation = Variation.objects.get(
                        product=product, variation_category__iexact=key, variation_value__ixact=value)
                    product_variation.append(variation)
                except:
                    pass

        try:
            cart = Cart.objects.get(cart_id=_cart_id(request))
        except Cart.DoesNotExist:
            cart = Cart.objects.create(
                cart_id=_cart_id(request)
            )
        cart.save()

        is_cart_item_exists = CartItem.objects.filter(
            product=product, cart=cart).exists()
        # Insercion del record
        if is_cart_item_exists:
            cart_item = CartItem.objects.filter(product=product, cart=cart)
            # capturar los variations que vienen desde la base de datos

            ex_var_list = []
            id = []
            for item in cart_item:
                existing_variation = item.variations.all()
                ex_var_list.append(list(existing_variation))
                id.append(item.id)

            if product_variation in ex_var_list:
                index = ex_var_list.index(product_variation)
                item_id = id[index]
                item = CartItem.objects.get(product=product, id=item_id)
                item.quantity += 1
                item.save()
            else:
                item = CartItem.objects.create(
                    product=product, quantity=1, cart=cart)
                # Insertar cada variation al cartItem
                if len(product_variation) > 0:
                    item.variations.clear()
                    item.variations.add(*product_variation)
                item.save()

        else:
            cart_item = CartItem.objects.create(
                product=product,
                quantity=1,
                cart=cart,
            )
            if len(product_variation) > 0:
                cart_item.variations.clear()
                cart_item.variations.add(*product_variation)
            cart_item.save()
        
        return redirect('cart')


def remove_cart(request, product_id, cart_item_id):
    
    product = get_object_or_404(Product, id=product_id)

    try:
        if request.user.is_authenticated:
            cart_item = CartItem.objects.get(product=product, user=request.user, id=cart_item_id)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)
        
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
    except:
        pass
    return redirect('cart')



    # Enviar las variaciones al carrtito de compras
    


def remove_cart_item(request, product_id, cart_item_id):
    product = get_object_or_404(Product, id=product_id)
    
    if request.user.is_authenticated:
        cart_item = CartItem.objects.get(product=product, user=request.user, id=cart_item_id)
    else:
        cart = Cart.objects.get(cart_id=_cart_id(request))    
        cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)
        cart_item.delete()
    
    return redirect('cart')


def cart(request, total=0, quantity=0, cart_items=None):
    iva = 0
    grand_total = 0
    try:

        #Condicion para saber si el user esta autenticado, para poder mostrar los item en carrito

        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)

        
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity

        iva = (12*total)/100
        grand_total = total + iva

    except ObjectDoesNotExist:
        pass  # solo ignora la excepcion

    context = {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'iva': iva,
        'grand_total': grand_total,
    }

    return render(request, 'store/cart.html', context)

@login_required(login_url='login')
def checkout(request,total=0, quantity=0, cart_items=None):
    iva = 0
    grand_total = 0
    try:
        
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)

        
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity

        iva = (12*total)/100
        grand_total = total + iva

    except ObjectDoesNotExist:
        pass  # solo ignora la excepcion

    context = {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'iva': iva,
        'grand_total': grand_total,
    }

    return render(request, 'store/checkout.html', context)



    


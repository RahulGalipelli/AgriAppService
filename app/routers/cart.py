from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.future import select
from app.db.session import async_session
from app.db.models.carts import Cart
from app.db.models.cart_items import CartItem
from app.db.models.products import Product
from app.core.security import get_current_user_id
from pydantic import BaseModel
from typing import List
from uuid import UUID

router = APIRouter(prefix="/cart", tags=["Cart"])


class CartItemRequest(BaseModel):
    product_id: str
    quantity: int


class CartItemResponse(BaseModel):
    product_id: str
    quantity: int
    product_name: str
    product_price: float

    class Config:
        from_attributes = True


class CartResponse(BaseModel):
    cart_id: str
    items: List[CartItemResponse]
    total: float


async def _get_cart_internal(session, user_id_uuid):
    """Internal function to get cart (used by other endpoints)"""
    # Get or create active cart
    result = await session.execute(
        select(Cart).where(Cart.user_id == user_id_uuid, Cart.is_active == True)
    )
    cart = result.scalar_one_or_none()

    if not cart:
        cart = Cart(user_id=user_id_uuid, is_active=True)
        session.add(cart)
        await session.commit()
        await session.refresh(cart)

    # Get cart items with product details
    items_result = await session.execute(
        select(CartItem, Product)
        .join(Product, CartItem.product_id == Product.id)
        .where(CartItem.cart_id == cart.id)
    )

    items = []
    total = 0.0
    for cart_item, product in items_result.all():
        item_total = float(product.price) * cart_item.quantity
        total += item_total
        items.append(CartItemResponse(
            product_id=str(cart_item.product_id),
            quantity=cart_item.quantity,
            product_name=product.name,
            product_price=float(product.price)
        ))

    return CartResponse(
        cart_id=str(cart.id),
        items=items,
        total=total
    )


@router.get("", response_model=CartResponse)
async def get_cart(user_id: str = Depends(get_current_user_id)):
    """Get user's cart"""
    async with async_session() as session:
        return await _get_cart_internal(session, UUID(user_id))


@router.post("/items", response_model=CartResponse)
async def add_to_cart(item: CartItemRequest, user_id: str = Depends(get_current_user_id)):
    """Add item to cart"""
    async with async_session() as session:
        # Get or create active cart
        result = await session.execute(
            select(Cart).where(Cart.user_id == UUID(user_id), Cart.is_active == True)
        )
        cart = result.scalar_one_or_none()

        if not cart:
            cart = Cart(user_id=UUID(user_id), is_active=True)
            session.add(cart)
            await session.commit()
            await session.refresh(cart)

        # Check if product exists
        product_result = await session.execute(
            select(Product).where(Product.id == UUID(item.product_id), Product.is_active == True)
        )
        product = product_result.scalar_one_or_none()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        # Add or update cart item
        item_result = await session.execute(
            select(CartItem).where(
                CartItem.cart_id == cart.id,
                CartItem.product_id == UUID(item.product_id)
            )
        )
        cart_item = item_result.scalar_one_or_none()

        if cart_item:
            cart_item.quantity = max(0, cart_item.quantity + item.quantity)
            if cart_item.quantity <= 0:
                await session.delete(cart_item)
        else:
            if item.quantity > 0:
                cart_item = CartItem(
                    cart_id=cart.id,
                    product_id=UUID(item.product_id),
                    quantity=max(1, item.quantity)
                )
                session.add(cart_item)

        await session.commit()

        # Return updated cart by fetching it
        return await _get_cart_internal(session, UUID(user_id))


@router.put("/items/{product_id}", response_model=CartResponse)
async def update_cart_item(
    product_id: str,
    quantity: int,
    user_id: str = Depends(get_current_user_id)
):
    """Update cart item quantity"""
    async with async_session() as session:
        # Get active cart
        result = await session.execute(
            select(Cart).where(Cart.user_id == UUID(user_id), Cart.is_active == True)
        )
        cart = result.scalar_one_or_none()
        if not cart:
            raise HTTPException(status_code=404, detail="Cart not found")

        if quantity <= 0:
            # Remove item
            item_result = await session.execute(
                select(CartItem).where(
                    CartItem.cart_id == cart.id,
                    CartItem.product_id == UUID(product_id)
                )
            )
            cart_item = item_result.scalar_one_or_none()
            if cart_item:
                await session.delete(cart_item)
        else:
            # Update quantity
            item_result = await session.execute(
                select(CartItem).where(
                    CartItem.cart_id == cart.id,
                    CartItem.product_id == UUID(product_id)
                )
            )
            cart_item = item_result.scalar_one_or_none()
            if cart_item:
                cart_item.quantity = quantity
            else:
                # Check if product exists
                product_result = await session.execute(
                    select(Product).where(Product.id == UUID(product_id), Product.is_active == True)
                )
                product = product_result.scalar_one_or_none()
                if not product:
                    raise HTTPException(status_code=404, detail="Product not found")
                
                cart_item = CartItem(
                    cart_id=cart.id,
                    product_id=UUID(product_id),
                    quantity=quantity
                )
                session.add(cart_item)

        await session.commit()
        return await get_cart(user_id)


@router.delete("/items/{product_id}", response_model=CartResponse)
async def remove_from_cart(product_id: str, user_id: str = Depends(get_current_user_id)):
    """Remove item from cart"""
    async with async_session() as session:
        result = await session.execute(
            select(Cart).where(Cart.user_id == UUID(user_id), Cart.is_active == True)
        )
        cart = result.scalar_one_or_none()
        if not cart:
            raise HTTPException(status_code=404, detail="Cart not found")

        item_result = await session.execute(
            select(CartItem).where(
                CartItem.cart_id == cart.id,
                CartItem.product_id == UUID(product_id)
            )
        )
        cart_item = item_result.scalar_one_or_none()
        if cart_item:
            await session.delete(cart_item)
            await session.commit()

        return await _get_cart_internal(session, UUID(user_id))


@router.delete("", response_model=dict)
async def clear_cart(user_id: str = Depends(get_current_user_id)):
    """Clear all items from cart"""
    async with async_session() as session:
        result = await session.execute(
            select(Cart).where(Cart.user_id == UUID(user_id), Cart.is_active == True)
        )
        cart = result.scalar_one_or_none()
        if cart:
            items_result = await session.execute(
                select(CartItem).where(CartItem.cart_id == cart.id)
            )
            for item in items_result.scalars().all():
                await session.delete(item)
            await session.commit()

        return {"success": True, "message": "Cart cleared"}


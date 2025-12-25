from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.future import select
from app.db.session import async_session
from app.db.models.orders import Order
from app.db.models.order_items import OrderItem
from app.db.models.carts import Cart
from app.db.models.cart_items import CartItem
from app.db.models.products import Product
from app.core.security import get_current_user_id
from pydantic import BaseModel
from typing import List
from uuid import UUID
from datetime import datetime

router = APIRouter(prefix="/orders", tags=["Orders"])


class CreateOrderRequest(BaseModel):
    address: str


class OrderItemResponse(BaseModel):
    product_id: str
    quantity: int
    price: float
    product_name: str

    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    id: str
    status: str
    total_amount: float
    address: str
    payment_method: str
    created_at: str
    items: List[OrderItemResponse]

    class Config:
        from_attributes = True


@router.post("", response_model=OrderResponse)
async def create_order(request: CreateOrderRequest, user_id: str = Depends(get_current_user_id)):
    """Create a new order from cart"""
    async with async_session() as session:
        # Get active cart
        cart_result = await session.execute(
            select(Cart).where(Cart.user_id == UUID(user_id), Cart.is_active == True)
        )
        cart = cart_result.scalar_one_or_none()
        
        if not cart:
            raise HTTPException(status_code=400, detail="Cart is empty")

        # Get cart items
        items_result = await session.execute(
            select(CartItem, Product)
            .join(Product, CartItem.product_id == Product.id)
            .where(CartItem.cart_id == cart.id)
        )

        cart_items = list(items_result.all())
        if not cart_items:
            raise HTTPException(status_code=400, detail="Cart is empty")

        # Calculate total
        total = sum(float(product.price) * cart_item.quantity for cart_item, product in cart_items)

        # Create order
        order = Order(
            user_id=UUID(user_id),
            status="placed",
            total_amount=total,
            address=request.address,
            created_at=datetime.utcnow()
        )
        session.add(order)
        await session.commit()
        await session.refresh(order)

        # Create order items
        order_items = []
        for cart_item, product in cart_items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=cart_item.product_id,
                quantity=cart_item.quantity,
                price=float(product.price)
            )
            session.add(order_item)
            order_items.append({
                "product_id": str(cart_item.product_id),
                "quantity": cart_item.quantity,
                "price": float(product.price),
                "product_name": product.name
            })

        # Clear cart
        for cart_item, _ in cart_items:
            await session.delete(cart_item)
        cart.is_active = False
        await session.commit()

        return OrderResponse(
            id=str(order.id),
            status=order.status,
            total_amount=float(order.total_amount),
            address=request.address,
            payment_method="COD",
            created_at=order.created_at.isoformat(),
            items=order_items
        )


@router.get("", response_model=List[OrderResponse])
async def get_orders(user_id: str = Depends(get_current_user_id)):
    """Get all orders for user"""
    async with async_session() as session:
        result = await session.execute(
            select(Order)
            .where(Order.user_id == UUID(user_id))
            .order_by(Order.created_at.desc())
        )
        orders = result.scalars().all()

        response = []
        for order in orders:
            # Get order items
            items_result = await session.execute(
                select(OrderItem, Product)
                .join(Product, OrderItem.product_id == Product.id)
                .where(OrderItem.order_id == order.id)
            )

            items = []
            for order_item, product in items_result.all():
                items.append(OrderItemResponse(
                    product_id=str(order_item.product_id),
                    quantity=order_item.quantity,
                    price=float(order_item.price),
                    product_name=product.name
                ))

            response.append(OrderResponse(
                id=str(order.id),
                status=order.status,
                total_amount=float(order.total_amount),
                address=order.address or "",
                payment_method="COD",
                created_at=order.created_at.isoformat(),
                items=items
            ))

        return response


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(order_id: str, user_id: str = Depends(get_current_user_id)):
    """Get a single order by ID"""
    async with async_session() as session:
        result = await session.execute(
            select(Order).where(Order.id == UUID(order_id), Order.user_id == UUID(user_id))
        )
        order = result.scalar_one_or_none()
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        # Get order items
        items_result = await session.execute(
            select(OrderItem, Product)
            .join(Product, OrderItem.product_id == Product.id)
            .where(OrderItem.order_id == order.id)
        )

        items = []
        for order_item, product in items_result.all():
            items.append(OrderItemResponse(
                product_id=str(order_item.product_id),
                quantity=order_item.quantity,
                price=float(order_item.price),
                product_name=product.name
            ))

        return OrderResponse(
            id=str(order.id),
            status=order.status,
            total_amount=float(order.total_amount),
            address=order.address or "",
            payment_method="COD",
            created_at=order.created_at.isoformat(),
            items=items
        )


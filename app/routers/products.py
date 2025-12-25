from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.future import select
from app.db.session import async_session
from app.db.models.products import Product
from app.db.models.product_images import ProductImage
from app.db.models.product_inventory import ProductInventory
from app.core.security import get_current_user_id
from typing import List
from pydantic import BaseModel

router = APIRouter(prefix="/products", tags=["Products"])


class ProductResponse(BaseModel):
    id: str
    name: str
    description: str | None
    price: float
    is_active: bool
    images: List[str] = []
    stock_quantity: int = 0
    unit: str | None = None

    class Config:
        from_attributes = True


@router.get("", response_model=List[ProductResponse])
async def get_products(user_id: str = Depends(get_current_user_id)):
    """Get all active products"""
    async with async_session() as session:
        result = await session.execute(
            select(Product).where(Product.is_active == True)
        )
        products = result.scalars().all()

        if not products:
            return []

        # Get inventory for each product
        product_ids = [p.id for p in products]
        inventory_result = await session.execute(
            select(ProductInventory).where(ProductInventory.product_id.in_(product_ids))
        )
        inventory_map = {inv.product_id: inv.quantity for inv in inventory_result.scalars().all()}

        # Get images for each product
        images_result = await session.execute(
            select(ProductImage).where(ProductImage.product_id.in_(product_ids))
        )
        images_map: dict = {}
        for img in images_result.scalars().all():
            if img.product_id not in images_map:
                images_map[img.product_id] = []
            images_map[img.product_id].append(img.image_url)

        response = []
        for product in products:
            response.append(ProductResponse(
                id=str(product.id),
                name=product.name,
                description=product.description,
                price=float(product.price),
                is_active=product.is_active,
                images=images_map.get(product.id, []),
                stock_quantity=inventory_map.get(product.id, 0),
                unit=None  # Unit not in model, can be added later
            ))

        return response


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: str, user_id: str = Depends(get_current_user_id)):
    """Get a single product by ID"""
    async with async_session() as session:
        result = await session.execute(
            select(Product).where(Product.id == product_id)
        )
        product = result.scalar_one_or_none()
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        # Get inventory
        inventory_result = await session.execute(
            select(ProductInventory).where(ProductInventory.product_id == product.id)
        )
        inventory = inventory_result.scalar_one_or_none()
        stock_quantity = inventory.quantity if inventory else 0

        # Get images
        images_result = await session.execute(
            select(ProductImage).where(ProductImage.product_id == product.id)
        )
        images = [img.image_url for img in images_result.scalars().all()]

        return ProductResponse(
            id=str(product.id),
            name=product.name,
            description=product.description,
            price=float(product.price),
            is_active=product.is_active,
            images=images,
            stock_quantity=stock_quantity,
            unit=None
        )


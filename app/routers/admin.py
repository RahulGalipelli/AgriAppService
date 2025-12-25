from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.future import select
from sqlalchemy import func, desc
from app.db.session import async_session
from app.db.models.users import User
from app.db.models.plant_scans import PlantScan
from app.db.models.orders import Order
from app.db.models.products import Product
from app.db.models.user_roles import UserRole
from app.core.security import get_current_user_id
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
from uuid import UUID

router = APIRouter(prefix="/admin", tags=["Admin"])


class AdminLoginRequest(BaseModel):
    email: str
    password: str


class AdminLoginResponse(BaseModel):
    access_token: str
    user: dict


class DashboardStatsResponse(BaseModel):
    total_uploads: int
    total_orders: int
    total_calls: int
    top_diseases: List[dict]


# Simple admin check - in production, use proper role-based access
async def get_admin_user(user_id: str = Depends(get_current_user_id)):
    async with async_session() as session:
        result = await session.execute(
            select(UserRole).where(UserRole.user_id == UUID(user_id), UserRole.role == "admin")
        )
        role = result.scalar_one_or_none()
        if not role:
            raise HTTPException(status_code=403, detail="Admin access required")
        return user_id


@router.post("/login", response_model=AdminLoginResponse)
async def admin_login(request: AdminLoginRequest):
    """Admin login - for now, simple email/password check"""
    # In production, use proper password hashing and verification
    if request.email == "admin@agricure.com" and request.password == "admin123":
        async with async_session() as session:
            # Get or create admin user
            result = await session.execute(select(User).where(User.phone == "0000000000"))
            admin_user = result.scalar_one_or_none()
            if not admin_user:
                admin_user = User(phone="0000000000", name="Admin", is_active=True)
                session.add(admin_user)
                await session.commit()
                await session.refresh(admin_user)
            
            # Create admin role if not exists
            role_result = await session.execute(
                select(UserRole).where(UserRole.user_id == admin_user.id, UserRole.role == "admin")
            )
            role = role_result.scalar_one_or_none()
            if not role:
                role = UserRole(user_id=admin_user.id, role="admin")
                session.add(role)
                await session.commit()
            
            from app.core.security import create_access_token
            access_token = create_access_token(subject=str(admin_user.id))
            
            return {
                "access_token": access_token,
                "user": {
                    "id": str(admin_user.id),
                    "email": request.email,
                    "name": admin_user.name or "Admin",
                    "role": "admin"
                }
            }
    raise HTTPException(status_code=401, detail="Invalid credentials")


@router.get("/me")
async def get_admin_info(user_id: str = Depends(get_admin_user)):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.id == UUID(user_id)))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {
            "id": str(user.id),
            "email": "admin@agricure.com",
            "name": user.name or "Admin",
            "role": "admin"
        }


@router.get("/dashboard/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(user_id: str = Depends(get_admin_user)):
    async with async_session() as session:
        # Total uploads
        uploads_result = await session.execute(select(func.count(PlantScan.id)))
        total_uploads = uploads_result.scalar() or 0
        
        # Total orders
        orders_result = await session.execute(select(func.count(Order.id)))
        total_orders = orders_result.scalar() or 0
        
        # Total calls (placeholder - would need a support_calls table)
        total_calls = 0
        
        # Top diseases
        from app.db.models.scan_results import ScanResult
        scans_result = await session.execute(
            select(ScanResult.result_json)
            .join(PlantScan, ScanResult.scan_id == PlantScan.id)
            .limit(100)
        )
        scans = scans_result.scalars().all()
        
        disease_counts = {}
        for scan_json in scans:
            if scan_json:
                import json
                if isinstance(scan_json, str):
                    try:
                        scan = json.loads(scan_json)
                    except:
                        continue
                else:
                    scan = scan_json
                
                if isinstance(scan, dict):
                    disease_name = scan.get("disease_name") or (scan.get("detections", [{}])[0].get("label") if scan.get("detections") else None) or "Unknown"
                    if disease_name and disease_name != "Unknown":
                        disease_counts[disease_name] = disease_counts.get(disease_name, 0) + 1
        
        top_diseases = [
            {"name": name, "count": count}
            for name, count in sorted(disease_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        ]
        
        return {
            "total_uploads": total_uploads,
            "total_orders": total_orders,
            "total_calls": total_calls,
            "top_diseases": top_diseases
        }


@router.get("/uploads")
async def get_all_uploads(user_id: str = Depends(get_admin_user)):
    from app.db.models.scan_results import ScanResult
    async with async_session() as session:
        result = await session.execute(
            select(PlantScan, User.phone, ScanResult)
            .join(User, PlantScan.user_id == User.id)
            .outerjoin(ScanResult, ScanResult.scan_id == PlantScan.id)
            .order_by(desc(PlantScan.created_at))
        )
        scans = result.all()
        
        uploads = []
        for scan, phone, scan_result in scans:
            result_data = {}
            if scan_result and scan_result.result_json:
                import json
                if isinstance(scan_result.result_json, str):
                    try:
                        result_data = json.loads(scan_result.result_json)
                    except:
                        result_data = {"raw": scan_result.result_json}
                else:
                    result_data = scan_result.result_json
            
            # Construct image URL (assuming images are stored in a static directory)
            image_url = f"/uploads/{scan.image_filename}" if scan.image_filename else ""
            
            uploads.append({
                "id": str(scan.id),
                "user_id": str(scan.user_id),
                "user_phone": phone or "Unknown",
                "image_url": image_url,
                "status": "completed" if scan_result else "pending",
                "result": result_data,
                "created_at": scan.created_at.isoformat() if scan.created_at else datetime.utcnow().isoformat()
            })
        
        return uploads


@router.get("/products")
async def get_all_products(user_id: str = Depends(get_admin_user)):
    async with async_session() as session:
        result = await session.execute(select(Product))
        products = result.scalars().all()
        
        from app.routers.products import ProductResponse
        from app.db.models.product_images import ProductImage
        from app.db.models.product_inventory import ProductInventory
        
        response = []
        for product in products:
            # Get images
            images_result = await session.execute(
                select(ProductImage).where(ProductImage.product_id == product.id)
            )
            images = [img.image_url for img in images_result.scalars().all()]
            
            # Get inventory
            inventory_result = await session.execute(
                select(ProductInventory).where(ProductInventory.product_id == product.id)
            )
            inventory = inventory_result.scalar_one_or_none()
            stock_quantity = inventory.quantity if inventory else 0
            
            response.append({
                "id": str(product.id),
                "name": product.name,
                "description": product.description,
                "price": float(product.price),
                "is_active": product.is_active,
                "images": images,
                "stock_quantity": stock_quantity,
                "unit": None
            })
        
        return response


@router.post("/products")
async def create_product(product_data: dict, user_id: str = Depends(get_admin_user)):
    async with async_session() as session:
        product = Product(
            name=product_data["name"],
            description=product_data.get("description"),
            price=product_data["price"],
            is_active=product_data.get("is_active", True)
        )
        session.add(product)
        await session.commit()
        await session.refresh(product)
        
        # Add inventory
        from app.db.models.product_inventory import ProductInventory
        inventory = ProductInventory(
            product_id=product.id,
            quantity=int(product_data.get("stock_quantity", 0))
        )
        session.add(inventory)
        await session.commit()
        
        return {"id": str(product.id), "message": "Product created successfully"}


@router.put("/products/{product_id}")
async def update_product(product_id: str, product_data: dict, user_id: str = Depends(get_admin_user)):
    async with async_session() as session:
        result = await session.execute(select(Product).where(Product.id == UUID(product_id)))
        product = result.scalar_one_or_none()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        product.name = product_data.get("name", product.name)
        product.description = product_data.get("description", product.description)
        product.price = product_data.get("price", product.price)
        product.is_active = product_data.get("is_active", product.is_active)
        
        # Update inventory
        from app.db.models.product_inventory import ProductInventory
        inventory_result = await session.execute(
            select(ProductInventory).where(ProductInventory.product_id == product.id)
        )
        inventory = inventory_result.scalar_one_or_none()
        if inventory:
            inventory.quantity = int(product_data.get("stock_quantity", inventory.quantity))
        else:
            inventory = ProductInventory(product_id=product.id, quantity=int(product_data.get("stock_quantity", 0)))
            session.add(inventory)
        
        await session.commit()
        return {"message": "Product updated successfully"}


@router.delete("/products/{product_id}")
async def delete_product(product_id: str, user_id: str = Depends(get_admin_user)):
    async with async_session() as session:
        result = await session.execute(select(Product).where(Product.id == UUID(product_id)))
        product = result.scalar_one_or_none()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        product.is_active = False
        await session.commit()
        return {"message": "Product deleted successfully"}


@router.get("/orders")
async def get_all_orders(user_id: str = Depends(get_admin_user)):
    async with async_session() as session:
        result = await session.execute(
            select(Order).order_by(desc(Order.created_at))
        )
        orders = result.scalars().all()
        
        from app.routers.orders import OrderResponse, OrderItemResponse
        from app.db.models.order_items import OrderItem
        from app.db.models.products import Product
        
        response = []
        for order in orders:
            items_result = await session.execute(
                select(OrderItem, Product)
                .join(Product, OrderItem.product_id == Product.id)
                .where(OrderItem.order_id == order.id)
            )
            
            items = []
            for order_item, product in items_result.all():
                items.append({
                    "product_id": str(order_item.product_id),
                    "quantity": order_item.quantity,
                    "price": float(order_item.price),
                    "product_name": product.name
                })
            
            response.append({
                "id": str(order.id),
                "user_id": str(order.user_id),
                "status": order.status,
                "total_amount": float(order.total_amount),
                "address": order.address or "",
                "payment_method": "COD",
                "created_at": order.created_at.isoformat() if order.created_at else datetime.utcnow().isoformat(),
                "items": items
            })
        
        return response


@router.put("/orders/{order_id}/status")
async def update_order_status(order_id: str, status_data: dict, user_id: str = Depends(get_admin_user)):
    async with async_session() as session:
        result = await session.execute(select(Order).where(Order.id == UUID(order_id)))
        order = result.scalar_one_or_none()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        order.status = status_data.get("status", order.status)
        await session.commit()
        return {"message": "Order status updated successfully"}


@router.get("/support/calls")
async def get_support_calls(user_id: str = Depends(get_admin_user)):
    # Placeholder - would need a support_calls table
    return []


@router.put("/support/calls/{call_id}/assign")
async def assign_support_call(call_id: str, assign_data: dict, user_id: str = Depends(get_admin_user)):
    # Placeholder
    return {"message": "Call assigned successfully"}


@router.put("/support/calls/{call_id}/resolve")
async def resolve_support_call(call_id: str, user_id: str = Depends(get_admin_user)):
    # Placeholder
    return {"message": "Call resolved successfully"}


@router.get("/analytics")
async def get_analytics(user_id: str = Depends(get_admin_user)):
    async with async_session() as session:
        # Region-wise diseases (placeholder - would need region data)
        region_wise_diseases = [
            {
                "region": "North",
                "diseases": [
                    {"name": "Leaf Blight", "count": 45},
                    {"name": "Root Rot", "count": 32}
                ]
            },
            {
                "region": "South",
                "diseases": [
                    {"name": "Powdery Mildew", "count": 38},
                    {"name": "Leaf Blight", "count": 28}
                ]
            }
        ]
        
        # Product conversion (placeholder)
        product_conversion = []
        
        # Farmer engagement (placeholder)
        farmer_engagement = []
        for i in range(6):
            month = (datetime.utcnow() - timedelta(days=30 * (5 - i))).strftime("%Y-%m")
            farmer_engagement.append({
                "month": month,
                "active_farmers": 100 + i * 10,
                "scans": 200 + i * 20,
                "orders": 50 + i * 5
            })
        
        return {
            "region_wise_diseases": region_wise_diseases,
            "product_conversion": product_conversion,
            "farmer_engagement": farmer_engagement
        }


@router.get("/settings")
async def get_settings(user_id: str = Depends(get_admin_user)):
    # Placeholder - would need a settings table
    return {
        "payment_gateway": {
            "provider": "razorpay",
            "api_key": "",
            "api_secret": "",
            "enabled": True
        },
        "courier_api": {
            "provider": "shiprocket",
            "api_key": "",
            "api_secret": "",
            "enabled": True
        },
        "push_notifications": {
            "fcm_server_key": "",
            "enabled": True
        }
    }


@router.put("/settings")
async def update_settings(settings_data: dict, user_id: str = Depends(get_admin_user)):
    # Placeholder - would save to settings table
    return {"message": "Settings updated successfully"}


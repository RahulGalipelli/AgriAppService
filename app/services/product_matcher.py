"""
Product Matcher Service
Matches diseases to available products and validates AI results
"""
import logging
from typing import List, Dict, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Product, ScanProductRecommendation
from uuid import UUID

logger = logging.getLogger(__name__)


class ProductMatcher:
    """Service for matching diseases to products"""
    
    # Disease-to-product mapping (can be expanded from database)
    DISEASE_PRODUCT_KEYWORDS = {
        'fungal': ['fungicide', 'antifungal', 'fungus'],
        'bacterial': ['bactericide', 'antibacterial', 'bacteria'],
        'viral': ['antiviral', 'virus'],
        'pest': ['pesticide', 'insecticide', 'pest'],
        'deficiency': ['fertilizer', 'nutrient', 'supplement'],
        'blight': ['fungicide', 'copper'],
        'rust': ['fungicide', 'rust'],
        'mildew': ['fungicide', 'mildew'],
        'aphid': ['insecticide', 'aphid'],
        'mite': ['miticide', 'mite'],
    }
    
    @staticmethod
    async def find_products_for_disease(
        session: AsyncSession,
        disease_name: str,
        limit: int = 5
    ) -> List[Product]:
        """
        Find products that match a given disease
        
        Args:
            session: Database session
            disease_name: Name of the disease
            limit: Maximum number of products to return
        
        Returns:
            List of matching products
        """
        disease_lower = disease_name.lower()
        
        # Extract keywords from disease name
        keywords = []
        for key, terms in ProductMatcher.DISEASE_PRODUCT_KEYWORDS.items():
            if any(term in disease_lower for term in terms):
                keywords.extend(terms)
        
        # Also use disease name itself as keyword
        keywords.append(disease_lower)
        
        # Search products by name and description
        query = select(Product).where(
            Product.is_active == True
        )
        
        result = await session.execute(query)
        all_products = result.scalars().all()
        
        # Score products based on keyword matches
        scored_products = []
        for product in all_products:
            score = 0
            product_text = f"{product.name} {product.description}".lower()
            
            for keyword in keywords:
                if keyword in product_text:
                    score += 1
            
            if score > 0:
                scored_products.append((score, product))
        
        # Sort by score (descending) and return top matches
        scored_products.sort(key=lambda x: x[0], reverse=True)
        return [product for _, product in scored_products[:limit]]
    
    @staticmethod
    async def validate_disease_has_products(
        session: AsyncSession,
        disease_name: str
    ) -> bool:
        """
        Check if we have products for a given disease
        
        Returns:
            True if products exist, False otherwise
        """
        products = await ProductMatcher.find_products_for_disease(
            session, disease_name, limit=1
        )
        return len(products) > 0
    
    @staticmethod
    async def suggest_alternative_diseases(
        session: AsyncSession,
        disease_name: str,
        limit: int = 3
    ) -> List[Dict]:
        """
        If no products found for disease, suggest similar diseases that have products
        
        Returns:
            List of alternative diseases with products
        """
        # Get all products
        query = select(Product).where(Product.is_active == True)
        result = await session.execute(query)
        all_products = result.scalars().all()
        
        # Find diseases mentioned in product descriptions
        disease_mentions = {}
        for product in all_products:
            product_text = (product.name + " " + (product.description or "")).lower()
            
            # Check against known disease keywords
            for disease_key, keywords in ProductMatcher.DISEASE_PRODUCT_KEYWORDS.items():
                if any(keyword in product_text for keyword in keywords):
                    if disease_key not in disease_mentions:
                        disease_mentions[disease_key] = []
                    disease_mentions[disease_key].append(product)
        
        # Return diseases with products (excluding the original)
        alternatives = []
        for disease, products in disease_mentions.items():
            if disease.lower() != disease_name.lower() and len(products) > 0:
                alternatives.append({
                    'disease_name': disease.title(),
                    'product_count': len(products),
                    'products': products[:limit]
                })
        
        # Sort by product count
        alternatives.sort(key=lambda x: x['product_count'], reverse=True)
        return alternatives[:limit]
    
    @staticmethod
    async def create_recommendations(
        session: AsyncSession,
        scan_id: UUID,
        disease_name: str
    ) -> None:
        """
        Create product recommendations for a scan
        
        Args:
            session: Database session
            scan_id: ID of the plant scan
            disease_name: Detected disease name
        """
        # Find matching products
        products = await ProductMatcher.find_products_for_disease(
            session, disease_name, limit=10
        )
        
        # Create recommendations
        for rank, product in enumerate(products, start=1):
            recommendation = ScanProductRecommendation(
                scan_id=scan_id,
                product_id=product.id,
                rank=rank
            )
            session.add(recommendation)
        
        await session.commit()


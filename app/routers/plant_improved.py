"""
Improved Plant Analysis Router with Hybrid AI System
Implements: Image hashing, consensus analysis, product matching
"""
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import os
from PIL import Image
import io
import base64
import json
import logging

from app.core.config import get_settings
from app.core.security import get_current_user_id
from app.db.models import PlantScan, ScanResult
from app.db.session import async_session
from app.services.image_hash_service import ImageHashService
from app.services.consensus_analyzer import ConsensusAnalyzer
from app.services.product_matcher import ProductMatcher
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

settings = get_settings()
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/plant", tags=["Plant"])

# Initialize services
image_hash_service = ImageHashService()
consensus_analyzer = ConsensusAnalyzer()


@router.post("/analyze")
async def analyze_plant(
    file: UploadFile = File(...), 
    user_id: str = Depends(get_current_user_id)
):
    """
    Analyze plant image with hybrid AI system:
    1. Check for duplicate/similar images
    2. Use consensus-based AI analysis
    3. Validate against product database
    4. Store results for future matching
    """
    print("Received file:", file.filename, file.content_type)
    contents = await file.read()

    if not contents or len(contents) < 1000:
        raise HTTPException(status_code=400, detail="Empty or invalid image file")

    try:
        image = Image.open(io.BytesIO(contents))
        image.verify()
    except Exception:
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid image")

    # Reopen image after verify
    image = Image.open(io.BytesIO(contents))
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

    async with async_session() as session:
        # Step 1: Generate image hashes
        try:
            phash, dct_hash = image_hash_service.generate_hash(contents)
            md5_hash = image_hash_service.generate_md5(contents)
        except Exception as e:
            logger.error(f"Failed to generate image hash: {str(e)}")
            phash = dct_hash = md5_hash = None

        # Step 2: Check for duplicate/similar images
        similar_scan = None
        if md5_hash:
            # Check for exact duplicate (MD5)
            query = select(PlantScan).where(PlantScan.image_hash_md5 == md5_hash)
            result = await session.execute(query)
            exact_duplicate = result.scalar_one_or_none()
            
            if exact_duplicate:
                # Get result from duplicate scan
                result_query = select(ScanResult).where(
                    ScanResult.scan_id == exact_duplicate.id
                )
                result_result = await session.execute(result_query)
                duplicate_result = result_result.scalar_one_or_none()
                
                if duplicate_result:
                    logger.info(f"Found exact duplicate scan: {exact_duplicate.id}")
                    return {
                        "scan_id": str(exact_duplicate.id),
                        "result": duplicate_result.result_json,
                        "is_duplicate": True,
                        "original_scan_id": str(exact_duplicate.id)
                    }
        
        # Check for similar images (perceptual hash)
        if phash:
            query = select(PlantScan).where(
                PlantScan.image_hash_phash.isnot(None)
            ).limit(100)  # Check recent scans for performance
            
            result = await session.execute(query)
            recent_scans = result.scalars().all()
            
            best_match = None
            best_similarity = 0.0
            
            for scan in recent_scans:
                if scan.image_hash_phash:
                    similarity = image_hash_service.calculate_similarity(
                        phash, scan.image_hash_phash
                    )
                    if similarity > best_similarity and similarity > 0.85:  # 85% similarity threshold
                        best_similarity = similarity
                        best_match = scan
            
            if best_match:
                # Get result from similar scan
                result_query = select(ScanResult).where(
                    ScanResult.scan_id == best_match.id
                )
                result_result = await session.execute(result_query)
                similar_result = result_result.scalar_one_or_none()
                
                if similar_result:
                    logger.info(f"Found similar scan: {best_match.id} (similarity: {best_similarity:.2f})")
                    similar_scan = best_match

        # Step 3: Run consensus-based AI analysis (if no similar match found)
        if not similar_scan:
            try:
                ai_result = await consensus_analyzer.analyze_with_consensus(
                    img_base64, num_runs=3
                )
            except Exception as e:
                logger.error(f"Consensus analysis failed: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
        else:
            # Use similar scan result
            ai_result = similar_result.result_json
            if isinstance(ai_result, str):
                try:
                    ai_result = json.loads(ai_result)
                except Exception:
                    ai_result = {"raw": ai_result}

        # Step 4: Validate against product database
        disease_name = ai_result.get('disease_name', 'Unknown')
        has_products = await ProductMatcher.validate_disease_has_products(
            session, disease_name
        )
        
        if not has_products:
            # Try to find alternative diseases with products
            alternatives = await ProductMatcher.suggest_alternative_diseases(
                session, disease_name, limit=3
            )
            if alternatives:
                ai_result['alternative_diseases'] = alternatives
                ai_result['note'] = f"No products found for '{disease_name}'. Consider these alternatives:"

        # Step 5: Create scan record
        scan = PlantScan(
            user_id=user_id,
            image_filename=file.filename,
            image_hash_phash=phash,
            image_hash_dct=dct_hash,
            image_hash_md5=md5_hash,
            is_duplicate=similar_scan is not None,
            original_scan_id=similar_scan.id if similar_scan else None
        )
        session.add(scan)
        await session.commit()
        await session.refresh(scan)
        
        # Step 6: Save the result
        scan_result = ScanResult(
            scan_id=scan.id,
            result_json=ai_result
        )
        session.add(scan_result)
        await session.commit()

        # Step 7: Create product recommendations
        try:
            await ProductMatcher.create_recommendations(
                session, scan.id, disease_name
            )
        except Exception as e:
            logger.error(f"Failed to create product recommendations: {str(e)}")

    return {
        "scan_id": str(scan.id),
        "result": ai_result,
        "is_duplicate": similar_scan is not None,
        "has_products": has_products
    }


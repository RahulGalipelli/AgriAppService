"""
Consensus-Based AI Analyzer
Runs multiple AI analyses in parallel and uses majority vote for consistency
"""
import json
import logging
import asyncio
from typing import Dict, List, Optional
from collections import Counter
from openai import OpenAI
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class ConsensusAnalyzer:
    """Analyzer that uses consensus from multiple AI runs"""
    
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY not found in environment")
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.num_runs = 3  # Number of times to run analysis
    
    async def analyze_with_consensus(
        self, 
        image_base64: str,
        num_runs: int = 3
    ) -> Dict:
        """
        Run AI analysis multiple times in parallel and return consensus result
        
        Args:
            image_base64: Base64 encoded image
            num_runs: Number of times to run analysis (default: 3)
        
        Returns:
            Dict with consensus result and confidence score
        """
        # Run all analyses in parallel for faster results
        tasks = [self._single_analysis(image_base64) for _ in range(num_runs)]
        
        try:
            # Execute all tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out exceptions and None results
            valid_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Analysis run {i+1} failed: {str(result)}")
                    continue
                if result:
                    valid_results.append(result)
            
            if not valid_results:
                raise ValueError("All analysis runs failed")
            
            results = valid_results
        except Exception as e:
            logger.error(f"Failed to run parallel analyses: {str(e)}")
            raise ValueError(f"Consensus analysis failed: {str(e)}")
        
        # Extract disease names
        disease_names = []
        for result in results:
            try:
                parsed = json.loads(result) if isinstance(result, str) else result
                disease_name = parsed.get('disease_name', 'Unknown')
                if disease_name and disease_name != 'Unknown':
                    disease_names.append(disease_name.lower().strip())
            except Exception:
                continue
        
        if not disease_names:
            # Fallback to first result if parsing fails
            return self._parse_result(results[0])
        
        # Find consensus (most common disease)
        disease_counts = Counter(disease_names)
        most_common = disease_counts.most_common(1)[0]
        consensus_disease = most_common[0]
        consensus_count = most_common[1]
        consensus_confidence = consensus_count / len(disease_names)
        
        # Find result with consensus disease
        consensus_result = None
        for result in results:
            try:
                parsed = json.loads(result) if isinstance(result, str) else result
                if parsed.get('disease_name', '').lower().strip() == consensus_disease:
                    consensus_result = parsed
                    break
            except Exception:
                continue
        
        # If no exact match, use first result but update disease name
        if not consensus_result:
            consensus_result = self._parse_result(results[0])
        
        # Update with consensus disease and confidence
        consensus_result['disease_name'] = consensus_disease.title()
        consensus_result['consensus_confidence'] = consensus_confidence
        consensus_result['consensus_count'] = consensus_count
        consensus_result['total_runs'] = len(results)
        consensus_result['needs_review'] = consensus_confidence < 0.67  # Flag if < 2/3 agreement
        
        return consensus_result
    
    async def _single_analysis(self, image_base64: str) -> str:
        """
        Run single AI analysis
        Note: OpenAI client is synchronous, so we run it in executor to make it non-blocking
        """
        try:
            # Run the synchronous OpenAI call in a thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.responses.create(
                    model="gpt-4.1-mini",
                    input=[
                        {
                            "role": "system",
                            "content": [
                                {
                                    "type": "input_text",
                                    "text": (
                                        "You are an agricultural disease detection API. "
                                        "Respond ONLY with raw JSON. Do not include markdown, text, or explanations. "
                                        "Keys: disease_name, confidence, symptoms, "
                                        "organic_treatment, chemical_treatment, prevention."
                                    )
                                }
                            ]
                        },
                        {
                            "role": "user",
                            "content": [
                                {"type": "input_text", "text": "Identify the plant disease"},
                                {
                                    "type": "input_image",
                                    "image_url": f"data:image/jpeg;base64,{image_base64}"
                                }
                            ]
                        }
                    ],
                    temperature=0,  # Set to 0 for more deterministic results
                )
            )
            return response.output_text
        except Exception as e:
            logger.error(f"OpenAI API call failed: {str(e)}")
            raise
    
    def _parse_result(self, result: str) -> Dict:
        """Parse AI result into structured format"""
        try:
            if isinstance(result, str):
                parsed = json.loads(result)
            else:
                parsed = result
            
            # Ensure all required fields exist
            return {
                'disease_name': parsed.get('disease_name', 'Unknown'),
                'confidence': parsed.get('confidence', 0.5),
                'symptoms': parsed.get('symptoms', ''),
                'organic_treatment': parsed.get('organic_treatment', ''),
                'chemical_treatment': parsed.get('chemical_treatment', ''),
                'prevention': parsed.get('prevention', ''),
                'next_steps': parsed.get('next_steps', [])
            }
        except Exception:
            return {
                'disease_name': 'Unknown',
                'confidence': 0.0,
                'symptoms': '',
                'organic_treatment': '',
                'chemical_treatment': '',
                'prevention': '',
                'next_steps': []
            }


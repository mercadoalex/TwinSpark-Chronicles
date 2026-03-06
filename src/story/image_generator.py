import os
import requests
import logging
from typing import Optional
import time

logger = logging.getLogger(__name__)


class ImageGenerator:
    """Generate child-friendly images using Leonardo.ai (150 FREE credits/month)"""
    
    def __init__(self):
        try:
            from config import settings
            self.api_key = getattr(settings, 'LEONARDO_API_KEY', None) or os.getenv('LEONARDO_API_KEY')
        except:
            self.api_key = os.getenv('LEONARDO_API_KEY')
        
        if self.api_key:
            self.api_url = "https://cloud.leonardo.ai/api/rest/v1/generations"
            self.headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            logger.info("✅ ImageGenerator initialized with Leonardo.ai (FREE)")
        else:
            logger.error("❌ NO LEONARDO API KEY - IMAGES REQUIRED FOR CHILDREN!")
            self.api_url = None
            self.headers = None
    
    def generate_scene(self, prompt: str) -> Optional[str]:
        """Generate child-friendly image with Leonardo.ai"""
        if not self.api_key:
            logger.error("❌ Cannot generate image - NO API KEY!")
            return None
        
        try:
            logger.info(f"🎨 [LEONARDO.AI] Generating: {prompt[:60]}...")
            
            # Optimized prompt for children
            child_friendly_prompt = (
                f"children's book illustration, cute cartoon, "
                f"bright vibrant colors, simple friendly characters, "
                f"pixar disney style, magical whimsical, safe for kids 4-8 years, "
                f"{prompt}"
            )
            
            payload = {
                "prompt": child_friendly_prompt,
                "negative_prompt": "scary, dark, violent, realistic, horror, adult, complex, detailed",
                "modelId": "6bef9f1b-29cb-40c7-b9df-32b51c1f67d3",  # Leonardo Anime XL (perfecto para niños)
                "width": 512,
                "height": 512,
                "num_images": 1,
                "guidance_scale": 7,
                "num_inference_steps": 30,
                "public": False,
                "nsfw": False
            }
            
            # Create generation
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code != 200:
                logger.error(f"❌ Failed to create generation: {response.status_code} - {response.text[:200]}")
                return None
            
            result = response.json()
            generation_id = result["sdGenerationJob"]["generationId"]
            
            logger.info(f"   ⏳ Generation ID: {generation_id}, waiting...")
            
            # Poll for result (Leonardo es rápido - 10-20s)
            get_url = f"https://cloud.leonardo.ai/api/rest/v1/generations/{generation_id}"
            
            for attempt in range(40):  # 40 segundos max
                time.sleep(1)
                
                poll_response = requests.get(get_url, headers=self.headers)
                
                if poll_response.status_code != 200:
                    logger.warning(f"⚠️ Poll failed: {poll_response.status_code}")
                    continue
                
                poll_data = poll_response.json()
                status = poll_data["generations_by_pk"]["status"]
                
                if status == "COMPLETE":
                    images = poll_data["generations_by_pk"]["generated_images"]
                    if images:
                        image_url = images[0]["url"]
                        
                        # Download and save
                        logger.info(f"   📥 Downloading from Leonardo...")
                        img_response = requests.get(image_url, timeout=20)
                        
                        assets_dir = os.path.join(
                            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                            "assets", "generated_images"
                        )
                        os.makedirs(assets_dir, exist_ok=True)
                        
                        filename = f"scene_{int(time.time())}.png"
                        filepath = os.path.join(assets_dir, filename)
                        
                        with open(filepath, "wb") as f:
                            f.write(img_response.content)
                        
                        local_url = f"/assets/generated_images/{filename}"
                        logger.info(f"✅ [CHILDREN IMAGE] Generated: {local_url}")
                        return local_url
                    
                elif status == "FAILED":
                    logger.error(f"❌ Generation failed")
                    return None
                
                if attempt % 5 == 0:
                    logger.info(f"   ⏳ Still generating... ({attempt}s, status: {status})")
            
            logger.warning("⚠️ Timeout after 40s")
            return None
                
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            return None
    
    def generate_character(self, name: str, gender: str, personality: list) -> Optional[str]:
        personality_str = ", ".join(personality) if isinstance(personality, list) else personality
        prompt = f"{name}, cute {gender} child character, {personality_str}, big eyes, smiling"
        return self.generate_scene(prompt)
    
    def generate_avatar(self, gender: str, personality: str) -> Optional[str]:
        prompt = f"simple avatar, {gender} child, {personality} personality, friendly face"
        return self.generate_scene(prompt)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("Initializing ImageGenerator Test...")
    
    try:
        generator = ImageGenerator()
        
        logger.info("\n--- Testing Avatar Generation ---")
        filepath = generator.generate_avatar("girl", "playful and creative")
        
        if filepath:
            logger.info(f"Test Successful! Image URL: {filepath}")
        else:
            logger.error("Test Failed: No image generated.")
                
    except Exception as e:
        logger.error(f"⚠️ Error during initialization or testing: {e}")

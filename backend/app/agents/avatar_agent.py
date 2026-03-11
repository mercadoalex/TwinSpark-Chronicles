# backend/app/agents/avatar_agent.py
import google.generativeai as genai
import base64
import io
from PIL import Image
from typing import Dict 
import os

class AvatarAgent:
    """
    Agent for generating child-friendly avatars using Imagen 3
    """
    
    def __init__(self):
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        
        # Note: Imagen 3 is still in preview, using Gemini Vision for now
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    async def generate_avatar(
        self,
        photo_base64: str,
        metadata: Dict
    ) -> Dict:
        """
        Generate child-friendly avatar from photo + metadata
        
        TODO: Replace with Imagen 3 when available
        For now, returns original photo with metadata
        """
        try:
            # Decode image
            image_data = photo_base64.split(',')[1] if ',' in photo_base64 else photo_base64
            image_bytes = base64.b64decode(image_data)
            img = Image.open(io.BytesIO(image_bytes))
            
            # TODO: Call Imagen 3 API
            # prompt = self._build_avatar_prompt(metadata)
            # avatar_image = await imagen.generate(prompt, reference_image=img)
            
            # For now, return original with processing flag
            return {
                "avatar_base64": photo_base64,
                "avatar_url": None,
                "metadata": {
                    **metadata,
                    "processed": False,
                    "message": "AI avatar generation coming soon! Using original photo."
                }
            }
            
        except Exception as e:
            raise Exception(f"Avatar generation failed: {str(e)}")
    
    def _build_avatar_prompt(self, metadata: Dict) -> str:
        """Build prompt for Imagen 3"""
        return f"""
Create a whimsical, child-friendly cartoon avatar of a {metadata['gender']} child.
Style: Pixar-like, colorful, friendly, magical
Include subtle {metadata['spirit_animal']} characteristics (ears, colors, etc.)
Background: Simple gradient with sparkles
Age-appropriate: 3-8 years old
Safe, positive, encouraging aesthetic
"""


avatar_agent = AvatarAgent()

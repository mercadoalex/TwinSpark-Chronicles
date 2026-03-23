"""
Visual Storytelling Agent using Imagen 3
Generates personalized story illustrations
"""

import vertexai
from vertexai.preview.vision_models import ImageGenerationModel
import base64
import os
from typing import Dict, List, Optional
from io import BytesIO
from PIL import Image

class VisualStorytellingAgent:
    """
    Generates personalized story scene illustrations using Imagen 3
    """
    
    def __init__(self):
        project_id = os.getenv("GOOGLE_PROJECT_ID")
        location = os.getenv("GOOGLE_LOCATION", "us-central1")
        
        if project_id:
            vertexai.init(project=project_id, location=location)
            self.model = ImageGenerationModel.from_pretrained("imagen-3.0-generate-001")
            self.enabled = True
            print("✅ Visual agent initialized with Imagen 3")
        else:
            print("ℹ️  Visual agent disabled (set GOOGLE_PROJECT_ID to enable Imagen 3)")
            self.enabled = False
    
    async def generate_scene_image(
        self,
        story_context: Dict,
        child_profiles: Dict,
        scene_description: str
    ) -> Optional[str]:
        """
        Generate a personalized story scene illustration
        
        Args:
            story_context: Current story state
            child_profiles: Character information
            scene_description: What's happening in this scene
            
        Returns:
            Base64 encoded image or None if generation fails
        """
        if not self.enabled:
            return None
        
        try:
            prompt = self._build_visual_prompt(
                story_context,
                child_profiles,
                scene_description
            )
            
            print(f"🎨 Generating scene with Imagen 3...")
            
            # Generate image
            response = self.model.generate_images(
                prompt=prompt,
                number_of_images=1,
                aspect_ratio="16:9",
                safety_filter_level="block_most",
                person_generation="allow_adult"  # Since using child avatars as reference
            )
            
            if response.images:
                # Convert to base64
                image_bytes = response.images[0]._image_bytes
                image_base64 = base64.b64encode(image_bytes).decode('utf-8')
                
                print(f"✅ Scene generated successfully")
                
                return f"data:image/png;base64,{image_base64}"
            else:
                print("❌ No image generated")
                return None
                
        except Exception as e:
            print(f"❌ Visual generation error: {e}")
            return None
    
    def _build_visual_prompt(
        self,
        story_context: Dict,
        child_profiles: Dict,
        scene_description: str
    ) -> str:
        """
        Build Imagen 3 prompt for child-friendly story illustration
        """
        c1 = child_profiles.get("child1", {})
        c2 = child_profiles.get("child2", {})
        
        prompt = f"""
Whimsical children's book illustration in Pixar/Disney animation style:

SCENE: {scene_description}

CHARACTERS:
- {c1.get('name', 'Child 1')}: A {c1.get('gender', 'child')} character with {c1.get('spirit_animal', 'magical')} features (ears, tail, colors), {c1.get('costume_prompt', 'wearing adventure clothes')}, holding {c1.get('toy_name', 'a magical item')}
- {c2.get('name', 'Child 2')}: A {c2.get('gender', 'child')} character with {c2.get('spirit_animal', 'enchanted')} features (wings, patterns, colors), {c2.get('costume_prompt', 'wearing explorer outfit')}, carrying {c2.get('toy_name', 'a special tool')}

STYLE REQUIREMENTS:
- Bright, saturated colors (RGB: vibrant)
- Soft lighting with magical sparkles
- Child-friendly, no scary elements
- Warm, inviting atmosphere
- Ages 3-8 appropriate
- Professional children's book quality

COMPOSITION:
- Wide shot showing both characters
- Characters are the focus (60% of frame)
- Background: {story_context.get('setting', 'magical forest with glowing trees')}
- Include: {story_context.get('key_objects', 'sparkles and magical elements')}

MOOD: {story_context.get('mood', 'joyful, adventurous, safe')}

NO text, NO words, NO letters in the image.
"""
        
        return prompt.strip()
    
    def _create_placeholder_image(self, text: str) -> str:
        """
        Create a placeholder image if Imagen 3 is unavailable
        """
        img = Image.new('RGB', (800, 450), color=(168, 85, 247))
        
        # Convert to base64
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
        
        return f"data:image/png;base64,{img_base64}"


# Global instance
visual_agent = VisualStorytellingAgent()
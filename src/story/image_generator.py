import os
import requests
from PIL import Image
import io
import time

class ImageGenerator:
    def __init__(self):
        # Load API key directly from environment (must be set before running)
        api_key = os.getenv("HUGGINGFACE_API_KEY")
        if not api_key:
            raise ValueError("HUGGINGFACE_API_KEY environment variable not set. Please add it to your .env file or export it.")
            
        self.headers = {"Authorization": f"Bearer {api_key}"}
        
        # We will use a high-quality free Hugging Face model for generating images
        # FLUX.1-schnell is currently one of the best models available on the free Inference API
        self.api_url = "https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-schnell"
        
        # Ensure the assets directory exists for saving images
        self.assets_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "assets")
        os.makedirs(self.assets_dir, exist_ok=True)
        
    def generate_character(self, child_name, gender, personality_traits, outfit_directive="heroic outfit"):
        """Generates a character avatar based on their personality traits and gender."""
        prompt = (
            f"A high-quality 3D animated Pixar style character portrait of a {gender} child named {child_name}. "
            f"Their personality is: {', '.join(personality_traits)}. "
            f"They are wearing a {outfit_directive}. "
            "The background should be clean and colorful. Cinematic lighting, highly detailed, expressive face."
        )
        
        print(f"🎨 Generating avatar for {child_name}...")
        return self._generate_and_save(prompt, f"{child_name.lower()}_avatar_{int(time.time())}.png")

    def generate_scene(self, scene_description, characters_involved):
        """Generates a story scene vector/illustration."""
        prompt = (
            f"A beautiful storybook illustration for children. Style: vibrant, magical 2D vector art. "
            f"Scene: {scene_description} "
            f"Featuring: {', '.join(characters_involved)}. "
            "Whimsical, inviting, and age-appropriate for a 6-year-old."
        )
        
        print(f"🖼️ Generating scene: {scene_description[:30]}...")
        return self._generate_and_save(prompt, f"scene_{int(time.time())}.png")
        
    def _generate_and_save(self, prompt, filename):
        """Helper to call Hugging Face Inference API and save the result locally."""
        try:
            # Call the Hugging Face API
            payload = {"inputs": prompt}
            response = requests.post(self.api_url, headers=self.headers, json=payload)
            
            if response.status_code != 200:
                print(f"❌ Failed to generate image: {response.status_code} - {response.text}")
                return None
                
            # The result is raw bytes of the image
            image = Image.open(io.BytesIO(response.content))
            
            filepath = os.path.join(self.assets_dir, filename)
            image.save(filepath)
            
            print(f"✅ Successfully saved image to: {filepath}")
            return filepath
                
        except Exception as e:
            print(f"❌ Failed to generate image: {e}")
            return None


if __name__ == "__main__":
    print("Initializing ImageGenerator Test...")
    
    # Try loading the .env file locally if it exists
    # (assuming we are running from the project root)
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
        
    try:
        generator = ImageGenerator()
        
        print("\n--- Testing Avatar Generation ---")
        ale_traits = ["bold", "creative", "playful"]
        filepath = generator.generate_character("Ale", "girl", ale_traits, "superhero cape and mask")
        
        if filepath:
            print(f"Test Successful! Check your assets folder for the new image.")
            
            # Try to open the image using the default system viewer
            import platform
            try:
                if platform.system() == 'Darwin':       # macOS
                    os.system(f"open {filepath}")
                elif platform.system() == 'Windows':    # Windows
                    os.system(f"start {filepath}")
                else:                                   # linux variants
                    os.system(f"xdg-open {filepath}")
            except Exception:
                pass 
                
    except ValueError as e:
        print(f"\n⚠️ Setup Required: {e}")
        print("Please ensure your HUGGINGFACE_API_KEY is available in your shell or .env file.")

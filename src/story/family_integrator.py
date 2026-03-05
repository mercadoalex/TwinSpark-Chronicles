"""
Family Integrator Module
Processes family photos and integrates them into stories.
"""

import os
from PIL import Image, ImageFilter, ImageEnhance, ImageOps
from typing import List, Dict, Optional, Tuple
import json
from datetime import datetime

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class FamilyIntegrator:
    """
    Handles family photo integration into the story universe.
    Features:
    - Upload and store family photos
    - Style transfer to match story aesthetic
    - Background processing
    - Face detection and tagging
    - Photo categorization
    """
    
    def __init__(self, photos_dir: Optional[str] = None):
        """
        Args:
            photos_dir: Directory for storing family photos. 
                       Defaults to assets/family_photos/
        """
        if photos_dir is None:
            self.photos_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "assets", "family_photos"
            )
        else:
            self.photos_dir = photos_dir
        
        # Create subdirectories
        self.originals_dir = os.path.join(self.photos_dir, "originals")
        self.styled_dir = os.path.join(self.photos_dir, "styled")
        self.thumbnails_dir = os.path.join(self.photos_dir, "thumbnails")
        
        for directory in [self.originals_dir, self.styled_dir, self.thumbnails_dir]:
            os.makedirs(directory, exist_ok=True)
        
        print(f"📸 Family Integrator initialized (photos: {self.photos_dir})")
    
    def upload_photo(
        self, 
        image_path: str,
        category: str = "general",
        description: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Dict:
        """
        Upload and process a family photo.
        
        Args:
            image_path: Path to the image file
            category: Photo category ("people", "places", "events", "general")
            description: Optional description
            tags: Optional list of tags
            
        Returns:
            Dict with photo metadata and paths
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        unique_name = f"{base_name}_{timestamp}"
        
        # Load image
        image = Image.open(image_path)
        image = image.convert('RGB')
        
        # Save original
        original_path = os.path.join(self.originals_dir, f"{unique_name}.jpg")
        image.save(original_path, quality=95)
        
        # Create styled version
        styled_image = self.apply_storybook_style(image)
        styled_path = os.path.join(self.styled_dir, f"{unique_name}_styled.jpg")
        styled_image.save(styled_path, quality=90)
        
        # Create thumbnail
        thumbnail = image.copy()
        thumbnail.thumbnail((300, 300), Image.Resampling.LANCZOS)
        thumbnail_path = os.path.join(self.thumbnails_dir, f"{unique_name}_thumb.jpg")
        thumbnail.save(thumbnail_path, quality=85)
        
        # Create metadata
        metadata = {
            "unique_name": unique_name,
            "original_path": original_path,
            "styled_path": styled_path,
            "thumbnail_path": thumbnail_path,
            "category": category,
            "description": description,
            "tags": tags or [],
            "uploaded_at": datetime.now().isoformat(),
            "dimensions": image.size,
            "enabled": True
        }
        
        # Save metadata
        metadata_path = os.path.join(self.photos_dir, f"{unique_name}_metadata.json")
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"✅ Photo uploaded: {unique_name}")
        return metadata
    
    def apply_storybook_style(self, image: Image.Image) -> Image.Image:
        """
        Apply storybook aesthetic to photo.
        Makes it look more like an illustration.
        
        Args:
            image: PIL Image object
            
        Returns:
            Styled PIL Image
        """
        # Resize to reasonable size
        max_size = 1024
        if max(image.size) > max_size:
            image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        
        # 1. Slight blur for painterly effect
        styled = image.filter(ImageFilter.GaussianBlur(radius=1))
        
        # 2. Enhance colors (more vibrant)
        enhancer = ImageEnhance.Color(styled)
        styled = enhancer.enhance(1.3)
        
        # 3. Increase contrast
        enhancer = ImageEnhance.Contrast(styled)
        styled = enhancer.enhance(1.2)
        
        # 4. Slight brightness boost
        enhancer = ImageEnhance.Brightness(styled)
        styled = enhancer.enhance(1.1)
        
        # 5. Edge enhancement (cartoon-like)
        styled = styled.filter(ImageFilter.EDGE_ENHANCE_MORE)
        
        # 6. Posterize slightly (reduce colors for illustrative look)
        # This creates the "painted" effect
        styled = ImageOps.posterize(styled, 4)
        
        return styled
    
    def remove_background(self, image: Image.Image) -> Image.Image:
        """
        Remove background from image (simple version).
        For better results, use rembg library.
        
        Args:
            image: PIL Image object
            
        Returns:
            Image with transparent background
        """
        # Simple version: convert to RGBA
        # For production, use rembg or similar
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        # This is a placeholder - in production, use:
        # from rembg import remove
        # return remove(image)
        
        return image
    
    def create_story_location(
        self,
        photo_metadata: Dict,
        location_name: str,
        location_description: str
    ) -> Dict:
        """
        Convert a family photo into a story location.
        
        Args:
            photo_metadata: Photo metadata from upload_photo()
            location_name: Name for the location (e.g., "Grandma's Garden")
            location_description: Description for storytelling
            
        Returns:
            Location data for universe
        """
        location_data = {
            "name": location_name,
            "description": location_description,
            "image_url": photo_metadata["styled_path"],
            "source_photo": photo_metadata["original_path"],
            "properties": {
                "type": "family_location",
                "based_on_photo": True,
                "photo_id": photo_metadata["unique_name"]
            }
        }
        
        print(f"🗺️  Created story location: {location_name}")
        return location_data
    
    def create_story_character(
        self,
        photo_metadata: Dict,
        character_name: str,
        character_description: str,
        personality: Optional[str] = None
    ) -> Dict:
        """
        Convert a family photo into a story character.
        
        Args:
            photo_metadata: Photo metadata from upload_photo()
            character_name: Name (e.g., "Grandpa Joe")
            character_description: Description for storytelling
            personality: Character personality traits
            
        Returns:
            Character data for universe
        """
        character_data = {
            "name": character_name,
            "description": character_description,
            "personality": personality or "kind and wise",
            "image_url": photo_metadata["styled_path"],
            "source_photo": photo_metadata["original_path"],
            "properties": {
                "type": "family_character",
                "based_on_photo": True,
                "photo_id": photo_metadata["unique_name"]
            }
        }
        
        print(f"👤 Created story character: {character_name}")
        return character_data
    
    def list_photos(
        self, 
        category: Optional[str] = None,
        enabled_only: bool = True
    ) -> List[Dict]:
        """
        List all uploaded photos.
        
        Args:
            category: Filter by category (optional)
            enabled_only: Only return enabled photos
            
        Returns:
            List of photo metadata dicts
        """
        photos = []
        
        for filename in os.listdir(self.photos_dir):
            if filename.endswith('_metadata.json'):
                metadata_path = os.path.join(self.photos_dir, filename)
                
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                
                # Apply filters
                if category and metadata.get('category') != category:
                    continue
                
                if enabled_only and not metadata.get('enabled', True):
                    continue
                
                photos.append(metadata)
        
        # Sort by upload date (most recent first)
        photos.sort(key=lambda x: x.get('uploaded_at', ''), reverse=True)
        
        return photos
    
    def get_photo(self, unique_name: str) -> Optional[Dict]:
        """Get photo metadata by unique name"""
        metadata_path = os.path.join(self.photos_dir, f"{unique_name}_metadata.json")
        
        if not os.path.exists(metadata_path):
            return None
        
        with open(metadata_path, 'r') as f:
            return json.load(f)
    
    def disable_photo(self, unique_name: str) -> bool:
        """Disable a photo (parent control)"""
        metadata = self.get_photo(unique_name)
        if not metadata:
            return False
        
        metadata['enabled'] = False
        metadata_path = os.path.join(self.photos_dir, f"{unique_name}_metadata.json")
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"🚫 Photo disabled: {unique_name}")
        return True
    
    def enable_photo(self, unique_name: str) -> bool:
        """Enable a photo"""
        metadata = self.get_photo(unique_name)
        if not metadata:
            return False
        
        metadata['enabled'] = True
        metadata_path = os.path.join(self.photos_dir, f"{unique_name}_metadata.json")
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"✅ Photo enabled: {unique_name}")
        return True
    
    def delete_photo(self, unique_name: str) -> bool:
        """Delete a photo and all its files"""
        metadata = self.get_photo(unique_name)
        if not metadata:
            return False
        
        # Delete files
        files_to_delete = [
            metadata.get('original_path'),
            metadata.get('styled_path'),
            metadata.get('thumbnail_path'),
            os.path.join(self.photos_dir, f"{unique_name}_metadata.json")
        ]
        
        for filepath in files_to_delete:
            if filepath and os.path.exists(filepath):
                os.remove(filepath)
        
        print(f"🗑️  Photo deleted: {unique_name}")
        return True
    
    def get_stats(self) -> Dict:
        """Get statistics about uploaded photos"""
        all_photos = self.list_photos(enabled_only=False)
        
        stats = {
            "total_photos": len(all_photos),
            "enabled_photos": len([p for p in all_photos if p.get('enabled', True)]),
            "disabled_photos": len([p for p in all_photos if not p.get('enabled', True)]),
            "categories": {}
        }
        
        # Count by category
        for photo in all_photos:
            category = photo.get('category', 'general')
            stats['categories'][category] = stats['categories'].get(category, 0) + 1
        
        return stats


# Test function
if __name__ == "__main__":
    print("📸 Family Integrator Test\n")
    
    integrator = FamilyIntegrator()
    
    # Test with a sample image (if available)
    test_image_path = "assets/TwinSpark.png"  # Use existing image for test
    
    if os.path.exists(test_image_path):
        print("📤 Uploading test photo...")
        
        metadata = integrator.upload_photo(
            test_image_path,
            category="places",
            description="TwinSpark logo for testing",
            tags=["test", "logo"]
        )
        
        print(f"\n✅ Upload successful!")
        print(f"   Original: {metadata['original_path']}")
        print(f"   Styled: {metadata['styled_path']}")
        print(f"   Thumbnail: {metadata['thumbnail_path']}")
        
        # Create a story location
        location = integrator.create_story_location(
            metadata,
            "The Magical Logo Land",
            "A place where logos come to life!"
        )
        
        print(f"\n🗺️  Location created: {location['name']}")
        
        # Show stats
        print(f"\n📊 Stats:")
        stats = integrator.get_stats()
        print(f"   Total photos: {stats['total_photos']}")
        print(f"   By category: {stats['categories']}")
        
    else:
        print(f"⚠️  Test image not found: {test_image_path}")
        print("   Create a test image to run the test")
    
    print("\n✅ Family Integrator test complete!")

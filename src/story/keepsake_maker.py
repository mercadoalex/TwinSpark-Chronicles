"""
Keepsake Maker Module
Creates beautiful shareable "storybook pages" after each session.
Combines photos, illustrations, and story text into memorable keepsakes.
"""

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import os
from datetime import datetime
from typing import List, Optional, Tuple
import textwrap

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class KeepsakeMaker:
    """
    Creates beautiful storybook pages that combine:
    - Character avatars
    - Scene illustrations
    - Story text
    - Session metadata
    """
    
    def __init__(self, output_dir: Optional[str] = None):
        """
        Args:
            output_dir: Directory to save keepsakes. Defaults to assets/keepsakes/
        """
        if output_dir is None:
            self.output_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "assets", "keepsakes"
            )
        else:
            self.output_dir = output_dir
        
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Design settings
        self.PAGE_WIDTH = 1200
        self.PAGE_HEIGHT = 1600
        self.MARGIN = 60
        self.BACKGROUND_COLOR = "#FFF9F0"  # Warm cream
        self.TEXT_COLOR = "#2C3E50"  # Dark blue-gray
        self.ACCENT_COLOR = "#FF6B9D"  # Pink accent
        
        # Try to load nice fonts, fallback to default
        self.title_font = self._load_font("Arial", 48, bold=True)
        self.story_font = self._load_font("Arial", 28)
        self.meta_font = self._load_font("Arial", 20)
        self.names_font = self._load_font("Arial", 32, bold=True)
        
        print(f"📖 Keepsake Maker initialized (output: {self.output_dir})")
    
    def _load_font(self, font_name: str, size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
        """Try to load a system font, fallback to default"""
        try:
            # Try common font paths
            if bold:
                paths = [
                    f"/System/Library/Fonts/{font_name} Bold.ttc",
                    f"/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                    "arial.ttf"
                ]
            else:
                paths = [
                    f"/System/Library/Fonts/{font_name}.ttc",
                    f"/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                    "arial.ttf"
                ]
            
            for path in paths:
                if os.path.exists(path):
                    return ImageFont.truetype(path, size)
            
            # Fallback to default
            return ImageFont.load_default()
        except Exception as e:
            print(f"⚠️ Font loading error: {e}, using default")
            return ImageFont.load_default()
    
    def create_storybook_page(
        self,
        title: str,
        story_text: str,
        child1_name: str,
        child2_name: str,
        scene_image_path: Optional[str] = None,
        avatar1_path: Optional[str] = None,
        avatar2_path: Optional[str] = None,
        session_date: Optional[datetime] = None
    ) -> str:
        """
        Create a complete storybook page.
        
        Args:
            title: Story title
            story_text: Main story content
            child1_name: Name of first child
            child2_name: Name of second child
            scene_image_path: Path to scene illustration (optional)
            avatar1_path: Path to first child's avatar (optional)
            avatar2_path: Path to second child's avatar (optional)
            session_date: Date of session (defaults to now)
            
        Returns:
            Path to saved keepsake image
        """
        if session_date is None:
            session_date = datetime.now()
        
        # Create canvas
        page = Image.new('RGB', (self.PAGE_WIDTH, self.PAGE_HEIGHT), self.BACKGROUND_COLOR)
        draw = ImageDraw.Draw(page)
        
        current_y = self.MARGIN
        
        # 1. Draw decorative header
        current_y = self._draw_header(page, draw, title, current_y)
        
        # 2. Draw character avatars
        if avatar1_path or avatar2_path:
            current_y = self._draw_avatars(
                page, avatar1_path, avatar2_path, 
                child1_name, child2_name, current_y
            )
        
        # 3. Draw scene illustration (if provided)
        if scene_image_path and os.path.exists(scene_image_path):
            current_y = self._draw_scene(page, scene_image_path, current_y)
        
        # 4. Draw story text
        current_y = self._draw_story_text(page, draw, story_text, current_y)
        
        # 5. Draw footer with date and names
        self._draw_footer(page, draw, session_date, child1_name, child2_name)
        
        # Save keepsake
        filename = f"keepsake_{session_date.strftime('%Y%m%d_%H%M%S')}.png"
        output_path = os.path.join(self.output_dir, filename)
        
        # Apply subtle texture/filter for storybook feel
        page = self._apply_storybook_effect(page)
        
        page.save(output_path, quality=95)
        print(f"✨ Keepsake saved: {output_path}")
        
        return output_path
    
    def _draw_header(self, page: Image.Image, draw: ImageDraw.Draw, title: str, y_pos: int) -> int:
        """Draw decorative header with title"""
        # Draw border
        border_rect = [
            self.MARGIN, y_pos,
            self.PAGE_WIDTH - self.MARGIN, y_pos + 120
        ]
        draw.rounded_rectangle(border_rect, radius=15, fill=self.ACCENT_COLOR, outline=None)
        
        # Draw title
        title_bbox = draw.textbbox((0, 0), title, font=self.title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (self.PAGE_WIDTH - title_width) // 2
        
        draw.text(
            (title_x, y_pos + 35),
            title,
            fill="white",
            font=self.title_font
        )
        
        return y_pos + 150
    
    def _draw_avatars(
        self, 
        page: Image.Image, 
        avatar1_path: Optional[str], 
        avatar2_path: Optional[str],
        name1: str,
        name2: str,
        y_pos: int
    ) -> int:
        """Draw character avatars side by side"""
        avatar_size = 200
        spacing = 100
        
        total_width = avatar_size * 2 + spacing
        start_x = (self.PAGE_WIDTH - total_width) // 2
        
        # Draw first avatar
        if avatar1_path and os.path.exists(avatar1_path):
            self._draw_avatar(page, avatar1_path, start_x, y_pos, avatar_size, name1)
        
        # Draw second avatar
        if avatar2_path and os.path.exists(avatar2_path):
            self._draw_avatar(
                page, avatar2_path, 
                start_x + avatar_size + spacing, 
                y_pos, avatar_size, name2
            )
        
        return y_pos + avatar_size + 80
    
    def _draw_avatar(
        self, 
        page: Image.Image, 
        avatar_path: str, 
        x: int, 
        y: int, 
        size: int,
        name: str
    ):
        """Draw a single avatar with circular mask and name"""
        try:
            avatar = Image.open(avatar_path)
            avatar = avatar.convert('RGB')
            avatar = avatar.resize((size, size), Image.Resampling.LANCZOS)
            
            # Create circular mask
            mask = Image.new('L', (size, size), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.ellipse([0, 0, size, size], fill=255)
            
            # Apply mask
            output = Image.new('RGB', (size, size), self.BACKGROUND_COLOR)
            output.paste(avatar, (0, 0))
            
            # Paste onto page
            page.paste(output, (x, y), mask)
            
            # Draw name below
            draw = ImageDraw.Draw(page)
            name_bbox = draw.textbbox((0, 0), name, font=self.names_font)
            name_width = name_bbox[2] - name_bbox[0]
            name_x = x + (size - name_width) // 2
            
            draw.text(
                (name_x, y + size + 15),
                name,
                fill=self.ACCENT_COLOR,
                font=self.names_font
            )
            
        except Exception as e:
            print(f"⚠️ Error loading avatar {avatar_path}: {e}")
    
    def _draw_scene(self, page: Image.Image, scene_path: str, y_pos: int) -> int:
        """Draw scene illustration"""
        try:
            scene = Image.open(scene_path)
            scene = scene.convert('RGB')
            
            # Resize to fit
            max_width = self.PAGE_WIDTH - 2 * self.MARGIN
            max_height = 400
            
            scene.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            
            # Center horizontally
            x = (self.PAGE_WIDTH - scene.width) // 2
            
            # Add subtle border
            border = Image.new('RGB', (scene.width + 10, scene.height + 10), self.ACCENT_COLOR)
            border.paste(scene, (5, 5))
            
            page.paste(border, (x - 5, y_pos))
            
            return y_pos + scene.height + 60
            
        except Exception as e:
            print(f"⚠️ Error loading scene {scene_path}: {e}")
            return y_pos
    
    def _draw_story_text(self, page: Image.Image, draw: ImageDraw.Draw, text: str, y_pos: int) -> int:
        """Draw story text with proper wrapping"""
        # Wrap text
        max_width = self.PAGE_WIDTH - 2 * self.MARGIN - 40
        avg_char_width = 16  # Approximate for size 28 font
        chars_per_line = max_width // avg_char_width
        
        wrapped_lines = []
        for paragraph in text.split('\n'):
            if paragraph.strip():
                wrapped_lines.extend(textwrap.wrap(paragraph, width=chars_per_line))
                wrapped_lines.append('')  # Empty line between paragraphs
        
        # Draw text box background
        text_height = len(wrapped_lines) * 40
        text_box = [
            self.MARGIN + 20, y_pos,
            self.PAGE_WIDTH - self.MARGIN - 20, y_pos + text_height + 40
        ]
        draw.rounded_rectangle(text_box, radius=10, fill="white", outline=self.ACCENT_COLOR, width=3)
        
        # Draw text
        line_y = y_pos + 25
        for line in wrapped_lines:
            if line.strip():
                draw.text(
                    (self.MARGIN + 40, line_y),
                    line,
                    fill=self.TEXT_COLOR,
                    font=self.story_font
                )
            line_y += 40
        
        return line_y + 20
    
    def _draw_footer(
        self, 
        page: Image.Image, 
        draw: ImageDraw.Draw, 
        date: datetime,
        name1: str, 
        name2: str
    ):
        """Draw footer with date and attribution"""
        footer_y = self.PAGE_HEIGHT - self.MARGIN - 60
        
        # Date
        date_str = date.strftime("%B %d, %Y")
        draw.text(
            (self.MARGIN + 20, footer_y),
            f"📅 {date_str}",
            fill=self.TEXT_COLOR,
            font=self.meta_font
        )
        
        # Attribution
        attribution = f"A TwinSpark Chronicles adventure with {name1} & {name2} ✨"
        attr_bbox = draw.textbbox((0, 0), attribution, font=self.meta_font)
        attr_width = attr_bbox[2] - attr_bbox[0]
        attr_x = self.PAGE_WIDTH - self.MARGIN - 20 - attr_width
        
        draw.text(
            (attr_x, footer_y),
            attribution,
            fill=self.TEXT_COLOR,
            font=self.meta_font
        )
    
    def _apply_storybook_effect(self, image: Image.Image) -> Image.Image:
        """Apply subtle effects for storybook feel"""
        # Slight blur for soft edges
        image = image.filter(ImageFilter.SMOOTH_MORE)
        
        # Increase contrast slightly
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.1)
        
        # Warm up colors slightly
        enhancer = ImageEnhance.Color(image)
        image = enhancer.enhance(1.05)
        
        return image
    
    def create_quick_keepsake(
        self,
        title: str,
        story_excerpt: str,
        child1_name: str,
        child2_name: str
    ) -> str:
        """
        Create a quick keepsake without images.
        Useful when story generation is fast but image generation is slow.
        """
        return self.create_storybook_page(
            title=title,
            story_text=story_excerpt,
            child1_name=child1_name,
            child2_name=child2_name
        )


# Test function
if __name__ == "__main__":
    print("📖 Keepsake Maker Test\n")
    
    maker = KeepsakeMaker()
    
    # Create a test keepsake
    story_text = """
    Ale and Sofi discovered a magical garden hidden behind their house. 
    
    Flowers sparkled with rainbow colors, and butterflies made of light 
    danced around them. Ale, always bold, reached out to touch a glowing 
    rose, while Sofi carefully studied its magical patterns.
    
    "Look!" said Ale, "The rose is singing!"
    
    Sofi listened closely. "It's teaching us a spell to help the garden grow!"
    
    Together, they learned the magical words and the whole garden burst 
    into even more beautiful blooms. Their teamwork had created something 
    truly special.
    """
    
    keepsake_path = maker.create_quick_keepsake(
        title="The Magical Garden",
        story_excerpt=story_text,
        child1_name="Ale",
        child2_name="Sofi"
    )
    
    print(f"\n✨ Test keepsake created!")
    print(f"📁 Location: {keepsake_path}")
    print(f"\nYou can now use this keepsake in your stories! 🎨")

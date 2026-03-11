"""
World Manager Module
Maintains a persistent story universe across sessions.
Tracks locations, characters, items, and story continuity.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from dataclasses import dataclass

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database import Database, UniverseLocation, UniverseCharacter, UniverseItem, Child


@dataclass
class StoryCallback:
    """A reference to a past event that can be mentioned in stories"""
    event_type: str  # "location_discovery", "character_meeting", "item_acquisition", etc.
    description: str
    session_id: str
    timestamp: datetime


class WorldManager:
    """
    Manages the persistent story universe.
    Features:
    - Track discovered locations
    - Remember recurring characters
    - Item inventory system
    - Story callbacks and continuity
    - World state evolution
    """
    
    def __init__(self, database: Optional[Database] = None):
        """
        Args:
            database: Database instance. Creates new one if None.
        """
        if database is None:
            self.db = Database()
            self.db.create_all_tables()
            self.own_db = True
        else:
            self.db = database
            self.own_db = False
        
        print("🌍 World Manager initialized")
    
    # ==================== LOCATIONS ====================
    
    def add_location(
        self,
        name: str,
        description: str,
        image_url: Optional[str] = None,
        properties: Optional[Dict] = None
    ) -> int:
        """
        Add a new location to the story universe.
        
        Args:
            name: Location name (e.g., "Crystal Caves")
            description: Location description
            image_url: Optional image URL
            properties: Custom properties dict
            
        Returns:
            Location ID
        """
        session = self.db.get_session()
        
        try:
            # Check if location already exists
            existing = session.query(UniverseLocation).filter_by(name=name).first()
            if existing:
                print(f"⚠️  Location already exists: {name}")
                return existing.id
            
            # Create new location
            location = UniverseLocation(
                name=name,
                description=description,
                image_url=image_url,
                properties=properties or {}
            )
            
            session.add(location)
            session.commit()
            
            location_id = location.id
            print(f"✅ Location added: {name}")
            
            return location_id
            
        finally:
            session.close()
    
    def visit_location(self, name: str) -> bool:
        """
        Record a visit to a location (increments visit count).
        
        Args:
            name: Location name
            
        Returns:
            True if successful
        """
        session = self.db.get_session()
        
        try:
            location = session.query(UniverseLocation).filter_by(name=name).first()
            
            if not location:
                print(f"⚠️  Location not found: {name}")
                return False
            
            location.visit_count += 1
            location.last_visited = datetime.utcnow()
            session.commit()
            
            print(f"📍 Visited {name} (visit #{location.visit_count})")
            return True
            
        finally:
            session.close()
    
    def get_location(self, name: str) -> Optional[Dict]:
        """Get location by name"""
        session = self.db.get_session()
        
        try:
            location = session.query(UniverseLocation).filter_by(name=name).first()
            return location.to_dict() if location else None
        finally:
            session.close()
    
    def list_locations(self, min_visits: int = 0) -> List[Dict]:
        """
        List all locations.
        
        Args:
            min_visits: Minimum number of visits (for filtering)
            
        Returns:
            List of location dicts
        """
        session = self.db.get_session()
        
        try:
            query = session.query(UniverseLocation)
            
            if min_visits > 0:
                query = query.filter(UniverseLocation.visit_count >= min_visits)
            
            locations = query.order_by(UniverseLocation.visit_count.desc()).all()
            return [loc.to_dict() for loc in locations]
            
        finally:
            session.close()
    
    # ==================== CHARACTERS ====================
    
    def add_character(
        self,
        name: str,
        description: str,
        personality: Optional[str] = None,
        image_url: Optional[str] = None,
        properties: Optional[Dict] = None
    ) -> int:
        """
        Add a character to the story universe.
        
        Args:
            name: Character name
            description: Character description
            personality: Personality traits
            image_url: Optional image
            properties: Custom properties
            
        Returns:
            Character ID
        """
        session = self.db.get_session()
        
        try:
            # Check if exists
            existing = session.query(UniverseCharacter).filter_by(name=name).first()
            if existing:
                print(f"⚠️  Character already exists: {name}")
                return existing.id
            
            # Create character
            character = UniverseCharacter(
                name=name,
                description=description,
                personality=personality or "friendly",
                image_url=image_url,
                properties=properties or {}
            )
            
            session.add(character)
            session.commit()
            
            character_id = character.id
            print(f"✅ Character added: {name}")
            
            return character_id
            
        finally:
            session.close()
    
    def meet_character(self, name: str) -> bool:
        """
        Record a meeting with a character.
        
        Args:
            name: Character name
            
        Returns:
            True if successful
        """
        session = self.db.get_session()
        
        try:
            character = session.query(UniverseCharacter).filter_by(name=name).first()
            
            if not character:
                print(f"⚠️  Character not found: {name}")
                return False
            
            character.last_seen = datetime.utcnow()
            session.commit()
            
            print(f"👋 Met {name}")
            return True
            
        finally:
            session.close()
    
    def increase_relationship(self, name: str, amount: int = 10) -> bool:
        """
        Increase relationship level with a character.
        
        Args:
            name: Character name
            amount: Amount to increase (default: 10)
            
        Returns:
            True if successful
        """
        session = self.db.get_session()
        
        try:
            character = session.query(UniverseCharacter).filter_by(name=name).first()
            
            if not character:
                return False
            
            character.relationship_level = min(100, character.relationship_level + amount)
            session.commit()
            
            print(f"💖 Relationship with {name}: {character.relationship_level}/100")
            return True
            
        finally:
            session.close()
    
    def get_character(self, name: str) -> Optional[Dict]:
        """Get character by name"""
        session = self.db.get_session()
        
        try:
            character = session.query(UniverseCharacter).filter_by(name=name).first()
            return character.to_dict() if character else None
        finally:
            session.close()
    
    def list_characters(self, min_relationship: int = 0) -> List[Dict]:
        """
        List all characters.
        
        Args:
            min_relationship: Minimum relationship level
            
        Returns:
            List of character dicts
        """
        session = self.db.get_session()
        
        try:
            query = session.query(UniverseCharacter)
            
            if min_relationship > 0:
                query = query.filter(UniverseCharacter.relationship_level >= min_relationship)
            
            characters = query.order_by(UniverseCharacter.relationship_level.desc()).all()
            return [char.to_dict() for char in characters]
            
        finally:
            session.close()
    
    # ==================== ITEMS ====================
    
    def add_item(
        self,
        name: str,
        description: str,
        owner_child_id: Optional[int] = None,
        image_url: Optional[str] = None,
        properties: Optional[Dict] = None
    ) -> int:
        """
        Add an item to the universe.
        
        Args:
            name: Item name
            description: Item description
            owner_child_id: ID of child who owns it (optional)
            image_url: Optional image
            properties: Custom properties
            
        Returns:
            Item ID
        """
        session = self.db.get_session()
        
        try:
            item = UniverseItem(
                name=name,
                description=description,
                owner_id=owner_child_id,
                image_url=image_url,
                properties=properties or {}
            )
            
            session.add(item)
            session.commit()
            
            item_id = item.id
            print(f"✅ Item added: {name}")
            
            return item_id
            
        finally:
            session.close()
    
    def transfer_item(self, item_id: int, new_owner_id: Optional[int]) -> bool:
        """
        Transfer item ownership.
        
        Args:
            item_id: Item ID
            new_owner_id: New owner child ID (None = no owner)
            
        Returns:
            True if successful
        """
        session = self.db.get_session()
        
        try:
            item = session.query(UniverseItem).filter_by(id=item_id).first()
            
            if not item:
                return False
            
            item.owner_id = new_owner_id
            session.commit()
            
            print(f"📦 Item transferred: {item.name}")
            return True
            
        finally:
            session.close()
    
    def get_item(self, item_id: int) -> Optional[Dict]:
        """Get item by ID"""
        session = self.db.get_session()
        
        try:
            item = session.query(UniverseItem).filter_by(id=item_id).first()
            return item.to_dict() if item else None
        finally:
            session.close()
    
    def list_items(self, owner_child_id: Optional[int] = None) -> List[Dict]:
        """
        List items.
        
        Args:
            owner_child_id: Filter by owner (None = all items)
            
        Returns:
            List of item dicts
        """
        session = self.db.get_session()
        
        try:
            query = session.query(UniverseItem)
            
            if owner_child_id is not None:
                query = query.filter(UniverseItem.owner_id == owner_child_id)
            
            items = query.order_by(UniverseItem.acquired_at.desc()).all()
            return [item.to_dict() for item in items]
            
        finally:
            session.close()
    
    # ==================== STORY CONTINUITY ====================
    
    def get_story_callbacks(
        self,
        limit: int = 5
    ) -> List[StoryCallback]:
        """
        Get recent story callbacks for continuity.
        Returns interesting past events that can be referenced.
        
        Args:
            limit: Maximum number of callbacks
            
        Returns:
            List of StoryCallback objects
        """
        callbacks = []
        
        # Recent location discoveries
        locations = self.list_locations()
        for loc in locations[:2]:  # Top 2 most visited
            if loc['visit_count'] > 0:
                callbacks.append(StoryCallback(
                    event_type="location_visit",
                    description=f"You've been to {loc['name']} {loc['visit_count']} times",
                    session_id="previous",
                    timestamp=datetime.fromisoformat(loc['first_discovered']) if loc['first_discovered'] else datetime.now()
                ))
        
        # Character relationships
        characters = self.list_characters(min_relationship=30)
        for char in characters[:2]:  # Top 2 friends
            callbacks.append(StoryCallback(
                event_type="character_friendship",
                description=f"{char['name']} is a good friend (relationship: {char['relationship_level']}/100)",
                session_id="previous",
                timestamp=datetime.fromisoformat(char['first_met']) if char['first_met'] else datetime.now()
            ))
        
        # Sort by timestamp (most recent first)
        callbacks.sort(key=lambda x: x.timestamp, reverse=True)
        
        return callbacks[:limit]
    
    def generate_story_context(self) -> str:
        """
        Generate a context string for story generation.
        Includes relevant universe state for continuity.
        
        Returns:
            Context string for AI prompt
        """
        context_parts = []
        
        # Locations
        locations = self.list_locations(min_visits=1)
        if locations:
            loc_names = [loc['name'] for loc in locations[:5]]
            context_parts.append(f"Previously discovered locations: {', '.join(loc_names)}")
        
        # Characters
        characters = self.list_characters(min_relationship=20)
        if characters:
            char_names = [char['name'] for char in characters[:5]]
            context_parts.append(f"Known characters: {', '.join(char_names)}")
        
        # Items
        items = self.list_items()
        if items:
            item_names = [item['name'] for item in items[:5]]
            context_parts.append(f"Important items: {', '.join(item_names)}")
        
        return "\n".join(context_parts) if context_parts else "Starting a new adventure in an unexplored world."
    
    # ==================== STATS ====================
    
    def get_stats(self) -> Dict:
        """Get universe statistics"""
        return {
            "total_locations": len(self.list_locations()),
            "total_characters": len(self.list_characters()),
            "total_items": len(self.list_items()),
            "most_visited_location": self._get_most_visited_location(),
            "best_friend": self._get_best_friend()
        }
    
    def _get_most_visited_location(self) -> Optional[str]:
        """Get name of most visited location"""
        locations = self.list_locations()
        if locations:
            return locations[0]['name']
        return None
    
    def _get_best_friend(self) -> Optional[str]:
        """Get name of character with highest relationship"""
        characters = self.list_characters()
        if characters:
            return characters[0]['name']
        return None
    
    def cleanup(self):
        """Clean up resources"""
        if self.own_db:
            self.db.close()


# Test function
if __name__ == "__main__":
    print("🌍 World Manager Test\n")
    
    # Create world manager
    world = WorldManager()
    
    # Add locations
    print("1️⃣  Adding locations...")
    world.add_location(
        "Crystal Caves",
        "A magical cave system filled with glowing crystals",
        properties={"theme": "mystery", "danger_level": 2}
    )
    world.add_location(
        "Enchanted Forest",
        "A forest where the trees whisper secrets",
        properties={"theme": "nature", "danger_level": 1}
    )
    world.add_location(
        "Sky Castle",
        "A castle floating among the clouds",
        properties={"theme": "adventure", "danger_level": 3}
    )
    
    # Visit locations
    print("\n2️⃣  Visiting locations...")
    world.visit_location("Crystal Caves")
    world.visit_location("Crystal Caves")  # Visit twice
    world.visit_location("Enchanted Forest")
    
    # Add characters
    print("\n3️⃣  Adding characters...")
    world.add_character(
        "Sparkle the Dragon",
        "A friendly dragon who loves crystals",
        "kind and curious"
    )
    world.add_character(
        "Professor Owl",
        "A wise owl who teaches magic",
        "wise and patient"
    )
    
    # Build relationships
    print("\n4️⃣  Building relationships...")
    world.meet_character("Sparkle the Dragon")
    world.increase_relationship("Sparkle the Dragon", 30)
    world.increase_relationship("Professor Owl", 20)
    
    # Add items
    print("\n5️⃣  Adding items...")
    world.add_item(
        "Friendship Bracelet",
        "A magical bracelet that glows when friends are near",
        properties={"power": "friendship_detection"}
    )
    world.add_item(
        "Crystal Key",
        "A key made of pure crystal, found in the caves",
        properties={"unlocks": "secret_door"}
    )
    
    # Generate story context
    print("\n6️⃣  Story Context:")
    print("=" * 50)
    print(world.generate_story_context())
    print("=" * 50)
    
    # Get callbacks
    print("\n7️⃣  Story Callbacks:")
    callbacks = world.get_story_callbacks()
    for cb in callbacks:
        print(f"   - {cb.description}")
    
    # Show stats
    print("\n📊 Universe Stats:")
    stats = world.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    world.cleanup()
    
    print("\n✅ World Manager test complete!")

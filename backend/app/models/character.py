# backend/app/models/character.py
from pydantic import BaseModel
from typing import Optional

class CharacterData(BaseModel):
    name: str
    gender: str
    spirit_animal: str
    toy_name: Optional[str] = None
    toy_type: Optional[str] = None       # 'preset' | 'photo'
    toy_image_url: Optional[str] = None  # URL or preset key
    avatar_base64: Optional[str] = None

class TwinCharacters(BaseModel):
    child1: CharacterData
    child2: CharacterData

class StoryContext(BaseModel):
    characters: TwinCharacters
    session_id: str
    language: str = "en"
    previous_context: Optional[str] = None
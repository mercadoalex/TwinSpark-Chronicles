# backend/app/agents/storyteller_agent.py
import google.generativeai as genai
from typing import Dict, List, Optional
import os
from datetime import datetime

class StorytellerAgent:
    """
    Gemini 2.0 Agent for generating personalized interactive stories for twins
    """
    
    def __init__(self):
        # Configure Gemini API
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        
        # Use Gemini 2.0 Flash (optimized for speed and quality)
        self.model = genai.GenerativeModel(
            model_name='gemini-2.0-flash-exp',
            generation_config={
                "temperature": 0.9,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 2048,
            },
            safety_settings=[
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                }
            ]
        )
        
        # System prompt for child-friendly storytelling
        self.system_prompt = """
You are a magical storyteller for young children (ages 3-8). 
You create personalized, interactive adventures featuring twin characters.

RULES:
1. Stories must be 100% child-safe and age-appropriate
2. Use simple language, short sentences
3. Include the children's names and their favorite things
4. Make stories interactive (ask questions, suggest gestures)
5. Keep each story segment to 3-4 sentences
6. Use emojis and exclamations to keep it fun
7. End each segment with a choice or question for the children
8. Incorporate their spirit animals and toys naturally
9. Themes: friendship, kindness, problem-solving, creativity
10. NO violence, scary content, or complex themes

FORMAT:
- Narrative: 3-4 sentences of story
- Interactive element: Question or gesture prompt
- Keep it magical and encouraging!
"""
    
    async def generate_story_segment(
        self, 
        context: Dict,
        user_input: Optional[str] = None
    ) -> Dict:
        """
        Generate a story segment based on character context and user input
        """
        try:
            # Build personalized prompt
            prompt = self._build_prompt(context, user_input)
            
            # Generate content with Gemini
            response = await self.model.generate_content_async(prompt)
            
            # Parse and structure response
            story_segment = {
                "text": response.text,
                "timestamp": datetime.utcnow().isoformat(),
                "characters": context["characters"],
                "interactive": self._extract_interactive_element(response.text)
            }
            
            return story_segment
            
        except Exception as e:
            print(f"Error generating story: {e}")
            # Fallback story
            return self._fallback_story(context)
    
    def _build_prompt(self, context: Dict, user_input: Optional[str]) -> str:
        """Build personalized prompt from character context"""
        
        c1 = context["characters"]["child1"]
        c2 = context["characters"]["child2"]
        
        base_prompt = f"""
{self.system_prompt}

CHARACTER INFO:
- {c1["name"]} ({c1["gender"]}): Spirit Animal is {c1["spirit_animal"]}, loves {c1.get("toy_name", "adventures")}
- {c2["name"]} ({c2["gender"]}): Spirit Animal is {c2["spirit_animal"]}, loves {c2.get("toy_name", "exploring")}

"""
        
        if user_input:
            base_prompt += f"\nThe children said/did: {user_input}\n"
            base_prompt += "Continue the story based on their action.\n"
        else:
            base_prompt += "\nStart a new magical adventure for these twins!\n"
        
        base_prompt += "\nGenerate the next story segment (3-4 sentences + interactive element):"
        
        return base_prompt
    
    def _extract_interactive_element(self, story_text: str) -> Dict:
        """Extract questions or prompts from story text"""
        
        # Simple extraction (can be enhanced with regex or NLP)
        lines = story_text.split('\n')
        last_line = lines[-1] if lines else ""
        
        is_question = '?' in last_line
        
        return {
            "type": "question" if is_question else "prompt",
            "text": last_line,
            "expects_response": is_question
        }
    
    def _fallback_story(self, context: Dict) -> Dict:
        """Fallback story if generation fails"""
        c1_name = context["characters"]["child1"]["name"]
        c2_name = context["characters"]["child2"]["name"]
        
        return {
            "text": f"Once upon a time, {c1_name} and {c2_name} discovered a magical portal in their backyard! ✨ It sparkled with rainbow colors and made a gentle humming sound. 🌈 What do you think they should do? Should they step through the portal or look for clues first?",
            "timestamp": datetime.utcnow().isoformat(),
            "characters": context["characters"],
            "interactive": {
                "type": "question",
                "text": "Should they step through the portal or look for clues first?",
                "expects_response": True
            }
        }


# Initialize global agent instance
storyteller = StorytellerAgent()
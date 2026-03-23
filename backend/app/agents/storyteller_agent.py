# backend/app/agents/storyteller_agent.py
import google.generativeai as genai
from google.generativeai.types import StopCandidateException, BlockedPromptException
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
                    "threshold": "BLOCK_LOW_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_LOW_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_LOW_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_LOW_AND_ABOVE"
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
        user_input: Optional[str] = None,
        personality_context: Optional[Dict] = None,
        relationship_context: Optional[Dict] = None,
        skill_map_context: Optional[Dict] = None,
        narrative_directives: Optional[Dict] = None,
    ) -> Dict:
        """
        Generate a story segment based on character context and user input.

        Optional sibling dynamics kwargs are forwarded to ``_build_prompt``
        to enrich the Gemini prompt with personality, relationship, skill,
        and narrative directive sections.
        """
        try:
            # Build personalized prompt
            prompt = self._build_prompt(
                context,
                user_input,
                personality_context=personality_context,
                relationship_context=relationship_context,
                skill_map_context=skill_map_context,
                narrative_directives=narrative_directives,
            )

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

        except (StopCandidateException, BlockedPromptException) as e:
            print(f"Gemini blocked response due to safety settings: {e}")
            return self._fallback_story(context)
        except Exception as e:
            print(f"Error generating story: {e}")
            # Fallback story
            return self._fallback_story(context)
    
    def _build_prompt(
        self,
        context: Dict,
        user_input: Optional[str],
        personality_context: Optional[Dict] = None,
        relationship_context: Optional[Dict] = None,
        skill_map_context: Optional[Dict] = None,
        narrative_directives: Optional[Dict] = None,
    ) -> str:
        """Build personalized prompt from character context and optional
        sibling dynamics layers.

        New keyword arguments (all optional, default ``None``):
        - personality_context: dict with child_id keys mapping to trait/fear info
        - relationship_context: dict with leadership_balance, cooperation_score, etc.
        - skill_map_context: dict with complementary_pairs list
        - narrative_directives: dict returned by ``build_narrative_directives()``
          with keys ``directives``, ``protagonist_child_id``, ``child_roles``
        """

        c1 = context["characters"]["child1"]
        c2 = context["characters"]["child2"]

        c1_costume = c1.get("costume_prompt", "wearing adventure clothes")
        c2_costume = c2.get("costume_prompt", "wearing adventure clothes")

        base_prompt = f"""
    {self.system_prompt}

    CHARACTER INFO:
    - {c1["name"]} ({c1["gender"]}): Spirit Animal is {c1["spirit_animal"]}, loves {c1.get("toy_name", "adventures")}, {c1_costume}
    - {c2["name"]} ({c2["gender"]}): Spirit Animal is {c2["spirit_animal"]}, loves {c2.get("toy_name", "exploring")}, {c2_costume}

    """

        # ── PERSONALITY INSIGHTS (Req 5.1) ────────────────────────
        if personality_context is not None:
            base_prompt += "PERSONALITY INSIGHTS:\n"
            for child_id, info in personality_context.items():
                traits = info.get("dominant_traits", [])
                fears = info.get("fears", [])
                themes = info.get("preferred_themes", [])
                traits_str = ", ".join(traits) if traits else "still emerging"
                fears_str = ", ".join(fears) if fears else "none known"
                themes_str = ", ".join(themes) if themes else "general adventure"
                base_prompt += (
                    f"- {child_id}: dominant traits = {traits_str}; "
                    f"fears = {fears_str}; preferred themes = {themes_str}\n"
                )
            base_prompt += "\n"

        # ── RELATIONSHIP DYNAMICS (Req 5.1, 6.2) ─────────────────
        if relationship_context is not None:
            base_prompt += "RELATIONSHIP DYNAMICS:\n"
            lb = relationship_context.get("leadership_balance", 0.5)
            cs = relationship_context.get("cooperation_score", 0.5)
            es = relationship_context.get("emotional_synchrony", 0.5)
            conflicts = relationship_context.get("recent_conflicts", [])
            base_prompt += (
                f"- Leadership balance: {lb:.2f} (0.5 = equal)\n"
                f"- Cooperation score: {cs:.2f}\n"
                f"- Emotional synchrony: {es:.2f}\n"
            )
            if conflicts:
                base_prompt += f"- Recent conflicts: {len(conflicts)}\n"
            base_prompt += "\n"

        # ── COMPLEMENTARY SKILLS (Req 5.1, 5.4) ──────────────────
        if skill_map_context is not None:
            pairs = skill_map_context.get("complementary_pairs", [])
            if pairs:
                base_prompt += "COMPLEMENTARY SKILLS:\n"
                for pair in pairs:
                    base_prompt += (
                        f"- {pair.get('strength_holder_id', '?')} is strong in "
                        f"{pair.get('trait_dimension', '?')} while "
                        f"{pair.get('growth_area_holder_id', '?')} is growing; "
                        f"suggested scenario: {pair.get('suggested_scenario', 'collaborative task')}\n"
                    )
                base_prompt += "\n"

        # ── NARRATIVE DIRECTIVES (Req 5.2, 5.3, 5.4, 5.5, 7.1) ──
        if narrative_directives is not None:
            dirs = narrative_directives.get("directives", [])
            protagonist = narrative_directives.get("protagonist_child_id")
            child_roles = narrative_directives.get("child_roles", {})

            if dirs:
                base_prompt += "NARRATIVE DIRECTIVES:\n"
                for d in dirs:
                    base_prompt += f"- {d}\n"
                base_prompt += "\n"

            # Dual-child addressing with distinct roles (Req 6.1, 6.2)
            if child_roles:
                base_prompt += "CHILD ROLES FOR THIS MOMENT:\n"
                for cid, role in child_roles.items():
                    base_prompt += f"- {cid}: {role}\n"
                base_prompt += "\n"

            if protagonist:
                base_prompt += (
                    f"The protagonist for this story moment is {protagonist}. "
                    "Present both children as equally capable heroes (Req 7.4).\n\n"
                )

        # ── COLLABORATIVE DRAWING CONTEXT (Req 5.1, 5.2, 5.3) ─────────
        drawing_context = context.get("drawing_context")
        if drawing_context is not None:
            drawing_prompt = drawing_context.get("prompt", "")
            sibling_names = drawing_context.get("sibling_names", [])
            names_str = " and ".join(sibling_names) if sibling_names else f"{c1['name']} and {c2['name']}"
            base_prompt += "COLLABORATIVE DRAWING CONTEXT:\n"
            base_prompt += (
                f"{names_str} just finished a collaborative drawing together! "
                f"The drawing prompt was: \"{drawing_prompt}\"\n"
                f"In the next narration, reference this drawing activity and mention "
                f"both {names_str} by name. Describe how their creative teamwork "
                f"contributes to the adventure. Keep it magical and encouraging!\n\n"
            )

        # ── Dual-child prompt instructions (Req 6.1, 6.3, 6.4, 6.5) ──
        base_prompt += (
            f"IMPORTANT: Address both {c1['name']} and {c2['name']} by name "
            "in every interactive prompt. Assign each child a distinct role or "
            "action so they both participate.\n"
        )
        base_prompt += (
            "If only one child responds within 15 seconds, gently encourage "
            "the silent child by name to join in. For example: "
            f"\"We'd love to hear from you too, {c2['name']}! What do you think?\"\n"
        )

        # ── User input handling (Req 6.5) ─────────────────────────
        if user_input:
            # Check if input contains responses from both children
            if " and " in user_input or ";" in user_input or "both" in user_input.lower():
                base_prompt += (
                    f"\nBoth {c1['name']} and {c2['name']} responded: {user_input}\n"
                    "Acknowledge both children's contributions and weave both "
                    "responses into the next story moment.\n"
                )
            else:
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
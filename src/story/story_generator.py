"""
TwinSpark Chronicles - Story Generation Engine

Uses Google's Gemini API to generate dynamic, adaptive stories
based on the Twin Intelligence Engine's directives.
"""

import google.generativeai as genai
import logging
import sys
import os
from typing import Dict, List, Optional

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings
from models import StoryTheme, ChildProfile

logger = logging.getLogger(__name__)


class StoryGenerator:
    """
    Generates adaptive, dual-perspective narratives using Google's Gemini API.
    """
    
    def __init__(self):
        """Initialize the story generator with Google AI."""
        if settings.google_api_key:
            genai.configure(api_key=settings.google_api_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
            logger.info("Story generator initialized with Gemini API")
        else:
            self.model = None
            logger.warning("No Google API key found - story generation will use mock data")
    
    def _build_story_prompt(
        self,
        directive: Dict,
        previous_context: Optional[str] = None
    ) -> str:
        """
        Build a detailed prompt for Gemini based on Twin Intelligence directive.
        """
        child1 = directive["child1"]
        child2 = directive["child2"]
        relationship = directive["relationship"]
        
        prompt = f"""You are the TwinSpark Chronicles story engine, creating an interactive story for two siblings.

**Children:**
- **{child1['name']}** (Age 6): Currently feeling {child1['emotional_state']}
  - Personality: {', '.join(child1['personality_hints'])}
  - Role in this story: {child1['role']}
  - Special Powers: {', '.join(child1['powers'])}
  
- **{child2['name']}** (Age 6): Currently feeling {child2['emotional_state']}
  - Personality: {', '.join(child2['personality_hints'])}
  - Role in this story: {child2['role']}
  - Special Powers: {', '.join(child2['powers'])}

**Relationship Context:**
- These siblings complement each other: {relationship['complementary_strengths']}
- This story REQUIRES teamwork - each child's powers are essential
- Divergence recommended: {relationship['divergence_recommended']}

**Story Requirements:**
- Theme: {directive['theme']}
- Age-appropriate for 6-year-olds
- Positive, encouraging tone
- Include moments where BOTH children feel heroic
- Create scenarios where their different powers must work together
- Length: 10-15 interactive story beats

**Language Requirement**: 
- IMPORTANT: You MUST write the entire story, narration, perspectives, and interaction prompts in this language: **{directive.get('language', 'en')}**. Do not use English unless the requested string is 'en'.

{"**Previous Context:**" + previous_context if previous_context else ""}

Generate the BEGINNING of an interactive story (first 3 story beats). Include:
1. An engaging opening that introduces the adventure
2. A moment where {child1['name']}'s personality shines
3. A moment where {child2['name']}'s personality shines
4. A clear challenge that requires BOTH of them

Format as JSON:
{{
  "title": "Story Title",
  "opening": "Opening narration",
  "beats": [
    {{
      "narration": "What happens",
      "child1_perspective": "How {child1['name']} experiences this",
      "child2_perspective": "How {child2['name']} experiences this",
      "interaction_prompt": "Question or choice for the children"
    }}
  ]
}}
"""
        return prompt
    
    def generate_story_opening(
        self,
        directive: Dict
    ) -> Dict:
        """
        Generate the opening of a story based on Twin Intelligence directive.
        """
        if not self.model:
            # Return mock data for development
            return self._generate_mock_opening(directive)
        
        try:
            prompt = self._build_story_prompt(directive)
            response = self.model.generate_content(prompt)
            
            # Parse response (in production, use structured output)
            story_data = self._parse_story_response(response.text)
            
            logger.info(f"Generated story opening: {story_data.get('title', 'Untitled')}")
            return story_data
            
        except Exception as e:
            logger.error(f"Error generating story: {e}")
            return self._generate_mock_opening(directive)
    
    def generate_next_beat(
        self,
        directive: Dict,
        previous_beats: List[Dict],
        child_choices: Dict[str, str]
    ) -> Dict:
        """
        Generate the next story beat based on children's choices.
        """
        context = self._build_context_from_beats(previous_beats, child_choices)
        
        if not self.model:
            return self._generate_mock_beat(directive, child_choices)
        
        try:
            prompt = self._build_continuation_prompt(directive, context, child_choices)
            response = self.model.generate_content(prompt)
            
            beat_data = self._parse_beat_response(response.text)
            
            logger.info(f"Generated story beat {len(previous_beats) + 1}")
            return beat_data
            
        except Exception as e:
            logger.error(f"Error generating story beat: {e}")
            return self._generate_mock_beat(directive, child_choices)
    
    def generate_dual_perspective(
        self,
        base_narration: str,
        child1_context: Dict,
        child2_context: Dict
    ) -> tuple[str, str]:
        """
        Generate two different perspectives of the same story moment.
        
        This is KEY for the "Parallel Perspective Protocol".
        """
        if not self.model:
            return (
                f"{base_narration} ({child1_context['name']}'s view)",
                f"{base_narration} ({child2_context['name']}'s view)"
            )
        
        prompt = f"""Generate two different perspectives of this story moment:

Base narration: {base_narration}

**{child1_context['name']}'s Perspective:**
- Personality: {', '.join(child1_context.get('personality_hints', []))}
- Current emotion: {child1_context.get('emotional_state', 'calm')}

**{child2_context['name']}'s Perspective:**
- Personality: {', '.join(child2_context.get('personality_hints', []))}
- Current emotion: {child2_context.get('emotional_state', 'calm')}

Write the SAME moment from each child's unique viewpoint. Include:
- What they notice (based on personality)
- What they think (internal monologue)
- What they feel (emotions)

Keep each perspective 2-3 sentences, age-appropriate for 6-year-olds.
"""
        
        try:
            response = self.model.generate_content(prompt)
            # Parse the two perspectives (simplified - in production use structured output)
            text = response.text
            parts = text.split('\n\n')
            
            perspective1 = parts[0] if len(parts) > 0 else base_narration
            perspective2 = parts[1] if len(parts) > 1 else base_narration
            
            return (perspective1, perspective2)
            
        except Exception as e:
            logger.error(f"Error generating dual perspective: {e}")
            return (
                f"{base_narration} ({child1_context['name']}'s view)",
                f"{base_narration} ({child2_context['name']}'s view)"
            )
    
    # ==================== HELPER METHODS ====================
    
    def _build_context_from_beats(
        self,
        beats: List[Dict],
        choices: Dict[str, str]
    ) -> str:
        """Build context string from previous story beats."""
        if not beats:
            return ""
        
        context_parts = ["Previous story:"]
        for i, beat in enumerate(beats):
            context_parts.append(f"{i+1}. {beat.get('narration', '')}")
            if f"beat_{i}" in choices:
                context_parts.append(f"   Children chose: {choices[f'beat_{i}']}")
        
        return "\n".join(context_parts)
    
    def _build_continuation_prompt(
        self,
        directive: Dict,
        context: str,
        choices: Dict[str, str]
    ) -> str:
        """Build prompt for continuing the story."""
        return f"""Continue this story with the next beat.

{context}

Children's latest choices: {choices}

Generate the next story beat that:
1. Responds to their choices
2. Continues to require teamwork
3. Keeps both children engaged
4. Moves toward a satisfying resolution

**Language Requirement**: 
- IMPORTANT: You MUST write the narration, perspectives, and interaction prompts in this exact language: **{directive.get('language', 'en')}**. Do not use English unless the requested string is 'en'.

Format as before with narration, dual perspectives, and interaction prompt.
"""
    
    def _parse_story_response(self, response_text: str) -> Dict:
        """Parse Gemini's response into structured data."""
        # Simplified parsing - in production, use structured output or JSON parsing
        return {
            "title": "The Crystal Quest",
            "opening": response_text[:200] if len(response_text) > 200 else response_text,
            "beats": []
        }
    
    def _parse_beat_response(self, response_text: str) -> Dict:
        """Parse a story beat response."""
        return {
            "narration": response_text,
            "child1_perspective": response_text,
            "child2_perspective": response_text,
            "interaction_prompt": "What should they do next?"
        }
    
    # ==================== MOCK DATA (FOR DEVELOPMENT) ====================
    
    def _generate_mock_opening(self, directive: Dict) -> Dict:
        """Generate mock story for testing without API."""
        child1_name = directive["child1"]["name"]
        child2_name = directive["child2"]["name"]
        lang = directive.get("language", "en")
        
        if lang == 'es':
            return {
                "title": f"La Búsqueda de {child1_name} y {child2_name}",
                "opening": f"¡En un reino mágico donde el sol siempre brilla, dos amigos especiales llamados {child1_name} y {child2_name} descubrieron que tenían poderes increíbles!",
                "beats": [
                    {
                        "narration": f"Una mañana soleada, {child1_name} y {child2_name} estaban jugando en el jardín cuando escucharon una voz suave pidiendo ayuda.",
                        "child1_perspective": f"¡{child1_name} sintió una oleada de energía de súper fuerza y supo que alguien necesitaba ayuda!",
                        "child2_perspective": f"La lectura de patrones de {child2_name} ayudó a sentir de dónde venía la voz.",
                        "interaction_prompt": "¿Deberían seguir la voz hacia el Bosque de Maravillas, o revisar la Cueva de Cristal primero?"
                    }
                ]
            }
        elif lang == 'hi':
            return {
                "title": f"{child1_name} और {child2_name} की खोज",
                "opening": f"एक जादुई राज्य में जहां हमेशा धूप खिली रहती है, {child1_name} और {child2_name} नाम के दो खास दोस्तों को पता चला कि उनके पास अद्भुत शक्तियां हैं!",
                "beats": [
                    {
                        "narration": f"एक धूप वाली सुबह, {child1_name} और {child2_name} बगीचे में खेल रहे थे जब उन्होंने मदद के लिए पुकारती एक कोमल आवाज़ सुनी।",
                        "child1_perspective": f"{child1_name} को सुपर स्ट्रेंथ ऊर्जा की एक लहर महसूस हुई और उसे पता चला कि किसी को मदद चाहिए!",
                        "child2_perspective": f"{child2_name} के पैटर्न पढ़ने से यह पता लगाने में मदद मिली कि आवाज़ कहाँ से आ रही है।",
                        "interaction_prompt": "क्या आपको अचरज के जंगल में आवाज़ के पीछे जाना चाहिए, या पहले क्रिस्टल गुफा की जाँच करनी चाहिए?"
                    }
                ]
            }
        else:
            return {
                "title": f"The Quest of {child1_name} and {child2_name}",
                "opening": f"In a magical kingdom where the sun always shines, two special friends named {child1_name} and {child2_name} discovered they had incredible powers!",
                "beats": [
                    {
                        "narration": f"One sunny morning, {child1_name} and {child2_name} were playing in the garden when they heard a gentle voice calling for help.",
                        "child1_perspective": f"{child1_name} felt a surge of super_strength energy and knew someone needed help!",
                        "child2_perspective": f"{child2_name}'s pattern_reading helped sense where the voice was coming from.",
                        "interaction_prompt": "Should you follow the voice into the Forest of Wonder, or check the Crystal Cave first?"
                    }
                ]
            }
    
    def _generate_mock_beat(self, directive: Dict, choices: Dict) -> Dict:
        """Generate mock story beat for testing."""
        child1_name = directive["child1"]["name"]
        child2_name = directive["child2"]["name"]
        lang = directive.get("language", "en")
        
        if lang == 'es':
            return {
                "narration": f"¡{child1_name} y {child2_name} combinaron sus poderes de una manera increíble!",
                "child1_perspective": f"¡{child1_name} usó su habilidad especial en el momento justo!",
                "child2_perspective": f"¡{child2_name} sabía exactamente qué hacer para ayudar!",
                "interaction_prompt": "¿Qué pasa después? ¿Ya lo celebraron o continúan la aventura?"
            }
        elif lang == 'hi':
            return {
                "narration": f"{child1_name} और {child2_name} ने अपनी शक्तियों को एक अद्भुत तरीके से मिलाया!",
                "child1_perspective": f"{child1_name} ने सही समय पर अपनी विशेष क्षमता का उपयोग किया!",
                "child2_perspective": f"{child2_name} ठीक से जानता था कि मदद करने के लिए क्या करना है!",
                "interaction_prompt": "आगे क्या होता है? क्या आप जश्न मनाते हैं, या साहसिक कार्य जारी रखते हैं?"
            }
        else:
            return {
                "narration": f"{child1_name} and {child2_name} combined their powers in an amazing way!",
                "child1_perspective": f"{child1_name} used their special ability at just the right moment!",
                "child2_perspective": f"{child2_name} knew exactly what to do to help!",
                "interaction_prompt": "What happens next? Do you celebrate, or continue the adventure?"
            }
    
    def _generate_mock_story(self, directive: Dict) -> Dict:
        """Generate initial mock story with rich character profiles."""
        child1_name = directive["child1"]["name"]
        child2_name = directive["child2"]["name"]
        lang = directive.get("language", "en")
        
        # Extract rich profile data
        c1_spirit = directive["child1"].get("spirit_animal", "dragon")
        c2_spirit = directive["child2"].get("spirit_animal", "owl")
        c1_tool = directive["child1"].get("favorite_tool", "sword")
        c2_tool = directive["child2"].get("favorite_tool", "book")
        c1_outfit = directive["child1"].get("favorite_outfit", "knight_armor")
        c2_outfit = directive["child2"].get("favorite_outfit", "wizard_robe")
        c1_toy = directive["child1"].get("favorite_toy", "teddy_bear")
        c2_toy = directive["child2"].get("favorite_toy", "storybook")
        c1_toy_name = directive["child1"].get("toy_name")
        c2_toy_name = directive["child2"].get("toy_name")
        c1_place = directive["child1"].get("favorite_place", "castle")
        c2_place = directive["child2"].get("favorite_place", "forest")
        
        # Helper function to format names nicely
        def format_name(text: str) -> str:
            return text.replace('_', ' ').title()
        
        # Create personalized opening based on their preferences
        if lang == 'es':
            # Spanish version with rich personalization
            toy1_ref = f'"{c1_toy_name}"' if c1_toy_name else format_name(c1_toy)
            toy2_ref = f'"{c2_toy_name}"' if c2_toy_name else format_name(c2_toy)
            
            return {
                "title": f"La Búsqueda de {child1_name} y {child2_name}",
                "opening": f"En un {format_name(c1_place)} mágico donde la aventura nunca termina, vivía {child1_name}, un valiente héroe con espíritu de {format_name(c1_spirit)}. Vestido con su {format_name(c1_outfit)}, siempre llevaba su {format_name(c1_tool)} a su lado. No muy lejos, en el {format_name(c2_place)}, {child2_name} estudiaba antiguos secretos, con espíritu de {format_name(c2_spirit)}, usando su {format_name(c2_tool)} para descubrir misterios. ¡Juntos, descubrieron que tenían poderes increíbles!",
                "beats": [
                    {
                        "narration": f"Una mañana brillante, ambos héroes sintieron algo extraño. Una misteriosa llamada de ayuda resonó a través del reino.",
                        "child1_perspective": f"{child1_name} agarró su {format_name(c1_tool)} con fuerza. El espíritu del {format_name(c1_spirit)} rugió dentro, llenando su {format_name(c1_outfit)} con energía dorada. Recordó lo que {toy1_ref} siempre decía: '¡Sé valiente cuando otros tengan miedo!' Con súper fuerza fluyendo por sus brazos, {child1_name} estaba listo para actuar.",
                        "child2_perspective": f"{child2_name} sacó su {format_name(c2_tool)} y ajustó su {format_name(c2_outfit)}. El espíritu del {format_name(c2_spirit)} susurró sabiduría antigua. La lectura de patrones reveló algo importante: ¡esta no era una misión ordinaria! {child2_name} pensó en {toy2_ref} y supo que el trabajo en equipo sería clave.",
                        "interaction_prompt": f"¿Deberían {child1_name} usar su fuerza mientras {child2_name} busca pistas? ¿O deberían explorar el {format_name(c1_place)} y el {format_name(c2_place)} juntos?"
                    }
                ]
            }
        elif lang == 'hi':
            # Hindi version with rich personalization
            toy1_ref = f'"{c1_toy_name}"' if c1_toy_name else format_name(c1_toy)
            toy2_ref = f'"{c2_toy_name}"' if c2_toy_name else format_name(c2_toy)
            
            return {
                "title": f"{child1_name} और {child2_name} की खोज",
                "opening": f"एक जादुई {format_name(c1_place)} में जहां रोमांच कभी खत्म नहीं होता, {child1_name} रहते थे, एक बहादुर नायक जिनकी आत्मा {format_name(c1_spirit)} की थी। अपने {format_name(c1_outfit)} पहने, वे हमेशा अपना {format_name(c1_tool)} साथ रखते थे। दूर नहीं, {format_name(c2_place)} में, {child2_name} प्राचीन रहस्यों का अध्ययन करते थे, {format_name(c2_spirit)} की आत्मा के साथ, अपने {format_name(c2_tool)} का उपयोग करके रहस्यों को खोलते थे। साथ में, उन्हें पता चला कि उनके पास अद्भुत शक्तियां हैं!",
                "beats": [
                    {
                        "narration": f"एक चमकीली सुबह, दोनों नायकों ने कुछ अजीब महसूस किया। मदद के लिए एक रहस्यमय पुकार राज्य भर में गूंज उठी।",
                        "child1_perspective": f"{child1_name} ने अपना {format_name(c1_tool)} मजबूती से पकड़ा। {format_name(c1_spirit)} की आत्मा गर्जना की, उनके {format_name(c1_outfit)} को सुनहरी ऊर्जा से भर दिया। उन्हें याद आया कि {toy1_ref} हमेशा क्या कहते थे: 'जब दूसरे डरें तो बहादुर बनो!' सुपर स्ट्रेंथ उनकी बाहों में बहती हुई, {child1_name} कार्रवाई के लिए तैयार थे।",
                        "child2_perspective": f"{child2_name} ने अपना {format_name(c2_tool)} निकाला और अपना {format_name(c2_outfit)} ठीक किया। {format_name(c2_spirit)} की आत्मा ने प्राचीन ज्ञान फुसफुसाया। पैटर्न पढ़ने से कुछ महत्वपूर्ण पता चला: यह कोई साधारण मिशन नहीं था! {child2_name} ने {toy2_ref} के बारे में सोचा और जान गए कि टीम वर्क कुंजी होगी।",
                        "interaction_prompt": f"क्या {child1_name} को अपनी ताकत का उपयोग करना चाहिए जबकि {child2_name} सुराग ढूंढते हैं? या क्या उन्हें {format_name(c1_place)} और {format_name(c2_place)} को एक साथ तलाशना चाहिए?"
                    }
                ]
            }
        else:
            # English version with rich personalization
            toy1_ref = f'"{c1_toy_name}"' if c1_toy_name else f"their {format_name(c1_toy)}"
            toy2_ref = f'"{c2_toy_name}"' if c2_toy_name else f"their {format_name(c2_toy)}"
            
            return {
                "title": f"The Quest of {child1_name} and {child2_name}",
                "opening": f"In a magical {format_name(c1_place)} where adventure never ends, lived {child1_name}, a brave hero with the spirit of a {format_name(c1_spirit)}. Dressed in {format_name(c1_outfit)}, they always carried their {format_name(c1_tool)} by their side. Not far away, in the {format_name(c2_place)}, {child2_name} studied ancient secrets, with the spirit of a {format_name(c2_spirit)}, using their {format_name(c2_tool)} to unlock mysteries. Together, they discovered they had incredible powers!",
                "beats": [
                    {
                        "narration": f"One bright morning, both heroes felt something strange. A mysterious call for help echoed across the realm.",
                        "child1_perspective": f"{child1_name} gripped their {format_name(c1_tool)} tightly. The {format_name(c1_spirit)} spirit roared within, filling their {format_name(c1_outfit)} with golden energy. They remembered what {toy1_ref} always said: 'Be brave when others are scared!' With super_strength flowing through their arms, {child1_name} was ready to act.",
                        "child2_perspective": f"{child2_name} pulled out their {format_name(c2_tool)} and adjusted their {format_name(c2_outfit)}. The {format_name(c2_spirit)} spirit whispered ancient wisdom. Pattern_reading revealed something important—this was no ordinary mission! {child2_name} thought of {toy2_ref} and knew teamwork would be key.",
                        "interaction_prompt": f"Should {child1_name} use their strength while {child2_name} searches for clues? Or should they explore the {format_name(c1_place)} and {format_name(c2_place)} together?"
                    }
                ]
            }

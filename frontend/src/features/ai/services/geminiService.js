import { ENV } from '../../../shared/config';

/**
 * Service for interacting with Gemini 2.0 backend
 */
class GeminiService {
  constructor() {
    this.baseURL = ENV.API_URL;
    this.ws = null;
  }

  /**
   * Generate basic story segment
   */
  async generateStory(characters, sessionId, userInput = null, language = 'en') {
    try {
      const response = await fetch(`${this.baseURL}/api/story/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          characters,
          session_id: sessionId,
          language,
          user_input: userInput
        })
      });

      if (!response.ok) {
        throw new Error(`Story generation failed: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('GeminiService.generateStory error:', error);
      throw error;
    }
  }

  /**
   * Generate rich multimodal story moment (Phase 1)
   */
  async generateRichStory(characters, sessionId, userInput = null, language = 'en') {
    try {
      const url = `${this.baseURL}/api/story/generate-rich`;  // ← FIXED
      
      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          characters,
          session_id: sessionId,
          language,
          user_input: userInput
        })
      });

      if (!response.ok) {
        throw new Error(`Rich story generation failed: ${response.statusText}`);
      }

      const data = await response.json();
      
      return {
        text: data.text,
        image: data.image,
        audio: data.audio,
        interactive: data.interactive,
        memoriesUsed: data.memories_used,
        agentsUsed: data.agents_used,
        timestamp: data.timestamp
      };
    } catch (error) {
      console.error('generateRichStory error:', error);
      throw error;
    }
  }

  /**
   * Get session summary with all memories
   */
  async getSessionSummary(sessionId) {
    try {
      const response = await fetch(`${this.baseURL}/api/session/${sessionId}/summary`);
      
      if (!response.ok) {
        throw new Error(`Failed to get session summary: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('getSessionSummary error:', error);
      throw error;
    }
  }

  /**
   * Connect to WebSocket for real-time storytelling
   */
  connectWebSocket(sessionId, onStorySegment, onError) {
    const wsURL = `${ENV.WS_URL}/ws/${sessionId}`;
    
    this.ws = new WebSocket(wsURL);
    
    this.ws.onopen = () => {
      console.log('✅ Connected to Gemini storytelling WebSocket');
    };
    
    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'story_segment') {
        onStorySegment(data.data);
      }
    };
    
    this.ws.onerror = (error) => {
      console.error('❌ WebSocket error:', error);
      if (onError) onError(error);
    };
    
    this.ws.onclose = () => {
      console.log('WebSocket closed');
    };
    
    return this.ws;
  }

  /**
   * Send user input through WebSocket
   */
  sendUserInput(context, userInput) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        context,
        user_input: userInput
      }));
    }
  }

  /**
   * Disconnect WebSocket
   */
  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

export const geminiService = new GeminiService();
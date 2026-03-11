import { useState, useEffect } from 'react';
import { geminiService } from '../services/geminiService';

/**
 * Hook for Gemini-powered story generation
 */
export function useStoryGeneration(characters, sessionId) {
  const [currentStory, setCurrentStory] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState(null);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    // Connect to WebSocket
    const ws = geminiService.connectWebSocket(
      sessionId,
      (storySegment) => {
        setCurrentStory(storySegment);
        setIsGenerating(false);
      },
      (err) => {
        setError(err.message);
        setIsGenerating(false);
      }
    );

    setIsConnected(true);

    // Cleanup
    return () => {
      geminiService.disconnect();
    };
  }, [sessionId]);

  const generateNextSegment = async (userInput = null) => {
    setIsGenerating(true);
    setError(null);

    try {
      const segment = await geminiService.generateStory(
        characters,
        sessionId,
        userInput
      );
      
      setCurrentStory(segment);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsGenerating(false);
    }
  };

  const sendInput = (userInput) => {
    geminiService.sendUserInput({ characters }, userInput);
  };

  return {
    currentStory,
    isGenerating,
    error,
    isConnected,
    generateNextSegment,
    sendInput
  };
}
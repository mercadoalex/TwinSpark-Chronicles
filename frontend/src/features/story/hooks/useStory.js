/**
 * useStory Hook
 * Manages story state and progression
 */

import { useState, useCallback } from 'react';
import { storyService } from '../services/storyService';

/**
 * Hook for managing story state
 * @param {Object} profiles - Character profiles
 * @returns {Object} Story utilities
 */
export function useStory(profiles) {
  const [currentBeat, setCurrentBeat] = useState(null);
  const [isComplete, setIsComplete] = useState(false);
  const [history, setHistory] = useState([]);

  /**
   * Add asset to current beat
   */
  const addAsset = useCallback((assetType, content, metadata = {}) => {
    const updatedAssets = storyService.addAsset(assetType, content, metadata);
    
    // Check if beat is complete
    if (storyService.isComplete()) {
      const beat = storyService.buildStoryBeat(profiles);
      setCurrentBeat(beat);
    }
    
    return updatedAssets;
  }, [profiles]);

  /**
   * Complete current beat and move to next
   */
  const completeBeat = useCallback((choice) => {
    if (currentBeat) {
      // Add to history
      setHistory(prev => [...prev, {
        ...currentBeat,
        choiceMade: choice,
        timestamp: new Date().toISOString()
      }]);
    }

    // Reset for next beat
    storyService.reset();
    setCurrentBeat(null);
  }, [currentBeat]);

  /**
   * Mark story as complete
   */
  const completeStory = useCallback(() => {
    setIsComplete(true);
    console.log('🎉 Story completed!');
  }, []);

  /**
   * Reset story
   */
  const reset = useCallback(() => {
    storyService.reset();
    setCurrentBeat(null);
    setIsComplete(false);
    setHistory([]);
    console.log('🔄 Story reset');
  }, []);

  /**
   * Get current assets
   */
  const getCurrentAssets = useCallback(() => {
    return storyService.getCurrentAssets();
  }, []);

  return {
    currentBeat,
    isComplete,
    history,
    addAsset,
    completeBeat,
    completeStory,
    reset,
    getCurrentAssets
  };
}
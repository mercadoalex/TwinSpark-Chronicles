/**
 * useStoryAssets Hook
 * Manages incremental asset accumulation for story beats
 */

import { useState, useCallback } from 'react';

/**
 * Hook for managing story assets accumulation
 * @returns {Object} Assets utilities
 */
export function useStoryAssets() {
  const [assets, setAssets] = useState({
    narration: '',
    child1_perspective: '',
    child2_perspective: '',
    image: null,
    choices: []
  });

  /**
   * Add text asset
   */
  const addText = useCallback((content, childId = null) => {
    setAssets(prev => {
      const updated = { ...prev };
      
      if (childId === 'c1') {
        updated.child1_perspective = content;
      } else if (childId === 'c2') {
        updated.child2_perspective = content;
      } else {
        updated.narration = content;
      }
      
      return updated;
    });
  }, []);

  /**
   * Add image asset
   */
  const addImage = useCallback((imageUrl) => {
    setAssets(prev => ({
      ...prev,
      image: imageUrl
    }));
  }, []);

  /**
   * Add choices
   */
  const addChoices = useCallback((choices) => {
    setAssets(prev => ({
      ...prev,
      choices: Array.isArray(choices) ? choices : []
    }));
  }, []);

  /**
   * Clear all assets
   */
  const clearAssets = useCallback(() => {
    setAssets({
      narration: '',
      child1_perspective: '',
      child2_perspective: '',
      image: null,
      choices: []
    });
  }, []);

  /**
   * Check if assets are complete
   */
  const isComplete = useCallback(() => {
    return !!(
      assets.narration &&
      assets.child1_perspective &&
      assets.child2_perspective &&
      assets.choices.length > 0
    );
  }, [assets]);

  return {
    assets,
    addText,
    addImage,
    addChoices,
    clearAssets,
    isComplete
  };
}
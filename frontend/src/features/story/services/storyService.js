/**
 * Story Service
 * Handles story asset aggregation and state management
 */

import { ASSET_TYPES } from '../../../shared/config';

/**
 * @typedef {Object} StoryAssets
 * @property {string} narration - Main narration text
 * @property {string} child1_perspective - Child 1's perspective
 * @property {string} child2_perspective - Child 2's perspective
 * @property {string | null} image - Image URL
 * @property {string[]} choices - Available choices
 * @property {Object} metadata - Additional metadata
 */

/**
 * @typedef {Object} StoryBeat
 * @property {string} narration - Main narration
 * @property {string} child1_perspective - Child 1's perspective
 * @property {string} child2_perspective - Child 2's perspective
 * @property {string | null} scene_image_url - Scene image URL
 * @property {string[]} choices - Available choices
 * @property {Object} [metadata] - Additional metadata
 */

class StoryService {
  constructor() {
    /** @type {StoryAssets} */
    this.currentAssets = this.createEmptyAssets();
  }

  /**
   * Create empty assets object
   * @returns {StoryAssets}
   */
  createEmptyAssets() {
    return {
      narration: '',
      child1_perspective: '',
      child2_perspective: '',
      image: null,
      choices: [],
      metadata: {}
    };
  }

  /**
   * Add an asset to current beat
   * @param {string} assetType - Type of asset (text, image, interactive)
   * @param {any} content - Asset content
   * @param {Object} [metadata={}] - Additional metadata
   * @returns {StoryAssets} Updated assets
   */
  addAsset(assetType, content, metadata = {}) {
    console.log(`📦 Adding asset: ${assetType}`, { content, metadata });

    switch (assetType) {
      case ASSET_TYPES.TEXT:
        this.handleTextAsset(content, metadata);
        break;
        
      case ASSET_TYPES.IMAGE:
        this.currentAssets.image = content;
        break;
        
      case ASSET_TYPES.INTERACTIVE:
        this.currentAssets.choices = this.parseChoices(content);
        break;
        
      default:
        console.warn(`⚠️ Unknown asset type: ${assetType}`);
    }

    return { ...this.currentAssets };
  }

  /**
   * Handle text asset (narration or perspective)
   * @param {string} content - Text content
   * @param {Object} metadata - Metadata
   */
  handleTextAsset(content, metadata) {
    if (metadata?.child === 'c1') {
      this.currentAssets.child1_perspective = content;
      console.log('→ Set as Child 1 perspective');
    } else if (metadata?.child === 'c2') {
      this.currentAssets.child2_perspective = content;
      console.log('→ Set as Child 2 perspective');
    } else {
      this.currentAssets.narration = content;
      console.log('→ Set as Narration');
    }
  }

  /**
   * Parse choices from various formats
   * @param {string | string[]} content - Choices content
   * @returns {string[]}
   */
  parseChoices(content) {
    if (Array.isArray(content)) {
      return content.filter(c => c && c.trim());
    }
    
    if (typeof content === 'string') {
      return content
        .split('\n')
        .map(line => line.trim())
        .filter(line => line && !line.match(/^\d+\./)) // Remove numbered lists
        .filter(line => !line.startsWith('-')) // Remove bullets
        .filter(line => !line.startsWith('•')) // Remove bullets
        .slice(0, 4); // Max 4 choices
    }
    
    return [];
  }

  /**
   * Build complete story beat from accumulated assets
   * @param {Object} profiles - Player profiles
   * @returns {StoryBeat}
   */
  buildStoryBeat(profiles) {
    const beat = {
      narration: this.currentAssets.narration || "The adventure begins...",
      child1_perspective: this.currentAssets.child1_perspective || 
        `${profiles?.c1_name || 'Child 1'} sees something magical...`,
      child2_perspective: this.currentAssets.child2_perspective || 
        `${profiles?.c2_name || 'Child 2'} feels excited...`,
      scene_image_url: this.currentAssets.image,
      choices: this.currentAssets.choices.length > 0 
        ? this.currentAssets.choices 
        : ["Continue the adventure"],
      metadata: this.currentAssets.metadata
    };

    console.log('🎬 Built story beat:', beat);
    return beat;
  }

  /**
   * Reset assets for new beat
   */
  reset() {
    console.log('🔄 Resetting story assets');
    this.currentAssets = this.createEmptyAssets();
  }

  /**
   * Get current assets (immutable copy)
   * @returns {StoryAssets}
   */
  getCurrentAssets() {
    return { ...this.currentAssets };
  }

  /**
   * Check if assets are complete
   * @returns {boolean}
   */
  isComplete() {
    return !!(
      this.currentAssets.narration &&
      this.currentAssets.child1_perspective &&
      this.currentAssets.child2_perspective &&
      this.currentAssets.choices.length > 0
    );
  }
}

export const storyService = new StoryService();
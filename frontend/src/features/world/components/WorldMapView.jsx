/**
 * WorldMapView — child-friendly world explorer for ages 6+.
 * Shows discovered locations, befriended NPCs, and collected items
 * with big colorful icons and minimal text.
 */

import React, { useEffect } from 'react';
import { useWorldStore } from '../../../stores/worldStore';
import { MapPin, Users, Backpack, X, Sparkles } from 'lucide-react';
import './WorldMapView.css';

const LOCATION_EMOJIS = ['🏰', '🌲', '🌊', '⛰️', '🌸', '🏝️', '🌋', '🎪', '🏠', '💎'];
const NPC_EMOJIS = ['🦊', '🦉', '🐉', '🦄', '🐬', '🧙', '🧚', '🐻', '🦁', '🐺'];
const ITEM_EMOJIS = ['⚔️', '🗝️', '🧭', '📜', '💍', '🔮', '🛡️', '🎵', '🌟', '🪄'];

function WorldMapView({ siblingPairId, onClose }) {
  const { locations, npcs, items, isLoading, fetchWorldState, isEmpty } = useWorldStore();

  useEffect(() => {
    if (siblingPairId) {
      fetchWorldState(siblingPairId);
    }
  }, [siblingPairId, fetchWorldState]);

  if (isLoading) {
    return (
      <div className="world-map-overlay">
        <div className="world-map-panel">
          <div className="world-map-loading">
            <Sparkles size={48} className="world-map-spinner" />
            <p>Loading your world...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="world-map-overlay">
      <div className="world-map-panel">
        <button className="world-map-close" onClick={onClose} aria-label="Close world map">
          <X size={28} />
        </button>

        <h2 className="world-map-title">🗺️ My World</h2>

        {isEmpty() ? (
          <div className="world-map-empty">
            <div className="world-map-empty-icon">🌟</div>
            <p className="world-map-empty-text">
              Start an adventure to discover your world! 🌟
            </p>
          </div>
        ) : (
          <div className="world-map-sections">
            {/* Locations */}
            {locations.length > 0 && (
              <section className="world-section">
                <h3 className="world-section-title">
                  <MapPin size={20} /> Places
                </h3>
                <div className="world-grid">
                  {locations.map((loc, i) => (
                    <div key={loc.id} className="world-card world-card--location">
                      <span className="world-card-emoji">
                        {LOCATION_EMOJIS[i % LOCATION_EMOJIS.length]}
                      </span>
                      <span className="world-card-name">{loc.name}</span>
                    </div>
                  ))}
                </div>
              </section>
            )}

            {/* NPCs */}
            {npcs.length > 0 && (
              <section className="world-section">
                <h3 className="world-section-title">
                  <Users size={20} /> Friends
                </h3>
                <div className="world-grid">
                  {npcs.map((npc, i) => (
                    <div key={npc.id} className="world-card world-card--npc">
                      <span className="world-card-emoji">
                        {NPC_EMOJIS[i % NPC_EMOJIS.length]}
                      </span>
                      <span className="world-card-name">{npc.name}</span>
                      <div className="world-card-hearts">
                        {'❤️'.repeat(Math.min(npc.relationship_level, 5))}
                      </div>
                    </div>
                  ))}
                </div>
              </section>
            )}

            {/* Items */}
            {items.length > 0 && (
              <section className="world-section">
                <h3 className="world-section-title">
                  <Backpack size={20} /> Treasures
                </h3>
                <div className="world-grid">
                  {items.map((item, i) => (
                    <div key={item.id} className="world-card world-card--item">
                      <span className="world-card-emoji">
                        {ITEM_EMOJIS[i % ITEM_EMOJIS.length]}
                      </span>
                      <span className="world-card-name">{item.name}</span>
                    </div>
                  ))}
                </div>
              </section>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default WorldMapView;

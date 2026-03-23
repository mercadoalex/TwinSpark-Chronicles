/**
 * Costume catalog — single source of truth for costume options.
 * Each entry: { id, label, emoji, color, promptFragment (≤20 words) }
 */
const costumeCatalog = [
  {
    id: 'knight_armor',
    label: 'Knight Armor',
    emoji: '⚔️',
    color: '#6366f1',
    promptFragment: 'wearing gleaming silver knight armor with a dragon crest shield',
  },
  {
    id: 'space_suit',
    label: 'Space Suit',
    emoji: '🚀',
    color: '#0ea5e9',
    promptFragment: 'wearing a shiny white space suit with a glowing helmet visor',
  },
  {
    id: 'princess_gown',
    label: 'Princess Gown',
    emoji: '👑',
    color: '#ec4899',
    promptFragment: 'wearing a sparkling pink princess gown with a golden tiara',
  },
  {
    id: 'pirate_outfit',
    label: 'Pirate Outfit',
    emoji: '🏴‍☠️',
    color: '#f59e0b',
    promptFragment: 'wearing a rugged pirate coat with a feathered tricorn hat',
  },
  {
    id: 'superhero_cape',
    label: 'Superhero Cape',
    emoji: '🦸',
    color: '#ef4444',
    promptFragment: 'wearing a bold superhero suit with a flowing red cape',
  },
  {
    id: 'wizard_robe',
    label: 'Wizard Robe',
    emoji: '🧙',
    color: '#8b5cf6',
    promptFragment: 'wearing a deep purple wizard robe covered in glowing star patterns',
  },
  {
    id: 'explorer_gear',
    label: 'Explorer Gear',
    emoji: '🧭',
    color: '#22c55e',
    promptFragment: 'wearing rugged explorer gear with a leather satchel and compass',
  },
  {
    id: 'fairy_wings',
    label: 'Fairy Wings',
    emoji: '🧚',
    color: '#a855f7',
    promptFragment: 'wearing a shimmering fairy outfit with translucent rainbow wings',
  },
];

export default costumeCatalog;

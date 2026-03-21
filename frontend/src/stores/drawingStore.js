/**
 * Drawing Store
 * Manages collaborative drawing session state, strokes, tools, and sync queue
 */

import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

// 8 child-friendly colors meeting >= 3:1 contrast ratio against #FFFFFF
export const PALETTE_COLORS = [
  '#E53935', // red
  '#D81B60', // pink
  '#8E24AA', // purple
  '#1E88E5', // blue
  '#00897B', // teal
  '#43A047', // green
  '#F4511E', // deep orange
  '#6D4C41', // brown
];

export const BRUSH_SIZES = { thin: 2, medium: 4, thick: 8 };

export const STAMP_SHAPES = ['star', 'heart', 'circle', 'lightning'];

export const DEFAULT_COLORS = {
  child1: '#E53935', // red
  child2: '#1E88E5', // blue
};

export const useDrawingStore = create(
  devtools(
    (set, get) => ({
      // State
      isActive: false,
      prompt: '',
      duration: 60,
      remainingTime: 60,
      strokes: [],
      undoStacks: { child1: [], child2: [] },
      selectedColor: PALETTE_COLORS[0],
      selectedBrushSize: 'medium',
      selectedTool: 'brush',
      selectedStamp: null,
      syncQueue: [],
      syncStatus: 'connected',

      // Actions

      startSession: (prompt, duration) =>
        set({
          isActive: true,
          prompt,
          duration,
          remainingTime: duration,
          strokes: [],
          undoStacks: { child1: [], child2: [] },
          syncQueue: [],
        }, false, 'drawing/startSession'),

      endSession: () =>
        set({ isActive: false }, false, 'drawing/endSession'),

      addStroke: (stroke) =>
        set((state) => ({
          strokes: [...state.strokes, stroke],
          undoStacks: {
            ...state.undoStacks,
            [stroke.sibling_id]: [
              ...(state.undoStacks[stroke.sibling_id] || []),
              stroke,
            ],
          },
        }), false, 'drawing/addStroke'),

      addRemoteStroke: (stroke) =>
        set((state) => ({
          strokes: [...state.strokes, stroke],
        }), false, 'drawing/addRemoteStroke'),

      undoLastStroke: (siblingId) => {
        const state = get();
        const stack = state.undoStacks[siblingId] || [];
        if (stack.length === 0) return;

        const removedStroke = stack[stack.length - 1];
        const newStack = stack.slice(0, -1);

        // Remove the last occurrence of this stroke from strokes array
        const strokeIdx = state.strokes.lastIndexOf(removedStroke);
        const newStrokes = strokeIdx >= 0
          ? [...state.strokes.slice(0, strokeIdx), ...state.strokes.slice(strokeIdx + 1)]
          : state.strokes;

        set({
          strokes: newStrokes,
          undoStacks: {
            ...state.undoStacks,
            [siblingId]: newStack,
          },
        }, false, 'drawing/undoLastStroke');
      },

      setColor: (color) =>
        set({ selectedColor: color }, false, 'drawing/setColor'),

      setBrushSize: (size) =>
        set({ selectedBrushSize: size }, false, 'drawing/setBrushSize'),

      setTool: (tool) =>
        set({ selectedTool: tool }, false, 'drawing/setTool'),

      setStamp: (stamp) =>
        set({ selectedStamp: stamp }, false, 'drawing/setStamp'),

      queueStroke: (stroke) =>
        set((state) => ({
          syncQueue: [...state.syncQueue, stroke],
        }), false, 'drawing/queueStroke'),

      flushSyncQueue: () => {
        const queue = get().syncQueue;
        set({ syncQueue: [] }, false, 'drawing/flushSyncQueue');
        return queue;
      },

      tick: () =>
        set((state) => {
          if (state.remainingTime <= 0) return {};
          const next = state.remainingTime - 1;
          if (next <= 0) {
            return { remainingTime: 0, isActive: false };
          }
          return { remainingTime: next };
        }, false, 'drawing/tick'),

      reset: () =>
        set({
          isActive: false,
          prompt: '',
          duration: 60,
          remainingTime: 60,
          strokes: [],
          undoStacks: { child1: [], child2: [] },
          selectedColor: PALETTE_COLORS[0],
          selectedBrushSize: 'medium',
          selectedTool: 'brush',
          selectedStamp: null,
          syncQueue: [],
          syncStatus: 'connected',
        }, false, 'drawing/reset'),
    }),
    { name: 'DrawingStore' }
  )
);

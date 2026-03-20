/**
 * Voice Recording Store
 * Manages voice recording state, uploads, and library browsing.
 */
import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

const API_BASE = 'http://localhost:8000';

export const useVoiceRecordingStore = create(
  devtools(
    (set, get) => ({
      // State
      recordings: [],
      isRecording: false,
      isUploading: false,
      recordingCount: 0,
      maxRecordings: 50,
      filters: { messageType: null, recorderName: null },
      loading: false,
      error: null,
      stats: null,
      commands: [],

      // Actions

      fetchRecordings: async (siblingPairId, filters = {}) => {
        if (!siblingPairId) return;
        set({ loading: true, error: null }, false, 'voiceRecording/fetchRecordings');
        try {
          const params = new URLSearchParams();
          const messageType = filters.messageType ?? get().filters.messageType;
          const recorderName = filters.recorderName ?? get().filters.recorderName;
          if (messageType) params.set('message_type', messageType);
          if (recorderName) params.set('recorder_name', recorderName);

          const qs = params.toString();
          const url = `${API_BASE}/api/voice-recordings/${siblingPairId}${qs ? `?${qs}` : ''}`;

          const [recordingsResp, statsResp] = await Promise.all([
            fetch(url),
            fetch(`${API_BASE}/api/voice-recordings/stats/${siblingPairId}`),
          ]);

          const recordings = recordingsResp.ok ? await recordingsResp.json() : [];
          const stats = statsResp.ok ? await statsResp.json() : null;

          set({
            recordings,
            stats,
            recordingCount: stats?.recording_count ?? recordings.length,
            loading: false,
          }, false, 'voiceRecording/fetchRecordings/done');
        } catch (err) {
          set({ loading: false, error: err.message }, false, 'voiceRecording/fetchRecordings/error');
        }
      },

      uploadRecording: async (siblingPairId, audioFile, metadata) => {
        set({ isUploading: true, error: null }, false, 'voiceRecording/upload');
        try {
          const formData = new FormData();
          formData.append('file', audioFile);
          formData.append('sibling_pair_id', siblingPairId);
          formData.append('recorder_name', metadata.recorderName);
          formData.append('relationship', metadata.relationship);
          formData.append('message_type', metadata.messageType);
          formData.append('language', metadata.language || 'en');
          if (metadata.commandPhrase) formData.append('command_phrase', metadata.commandPhrase);
          if (metadata.commandAction) formData.append('command_action', metadata.commandAction);

          const resp = await fetch(`${API_BASE}/api/voice-recordings/upload`, {
            method: 'POST',
            body: formData,
          });

          if (!resp.ok) {
            const body = await resp.json().catch(() => ({}));
            throw new Error(body.detail || 'Upload failed');
          }

          const result = await resp.json();
          // Refresh recordings list after successful upload
          await get().fetchRecordings(siblingPairId);
          set({ isUploading: false }, false, 'voiceRecording/upload/done');
          return { success: true, data: result };
        } catch (err) {
          set({ isUploading: false, error: err.message }, false, 'voiceRecording/upload/error');
          return { success: false, error: err.message };
        }
      },

      deleteRecording: async (recordingId, parentPin, siblingPairId) => {
        const prevRecordings = get().recordings;
        // Optimistic update — remove locally first
        set({
          recordings: prevRecordings.filter((r) => r.recording_id !== recordingId),
        }, false, 'voiceRecording/delete');
        try {
          const resp = await fetch(`${API_BASE}/api/voice-recordings/${recordingId}`, {
            method: 'DELETE',
            headers: { 'x-parent-pin': parentPin },
          });
          if (!resp.ok) {
            set({ recordings: prevRecordings }, false, 'voiceRecording/delete/revert');
            const body = await resp.json().catch(() => ({}));
            return { success: false, error: body.detail || 'Delete failed' };
          }
          const result = await resp.json();
          // Refresh stats after deletion
          if (siblingPairId) await get().fetchRecordings(siblingPairId);
          return { success: true, data: result };
        } catch (err) {
          set({ recordings: prevRecordings }, false, 'voiceRecording/delete/error');
          return { success: false, error: err.message };
        }
      },

      deleteAllRecordings: async (siblingPairId, parentPin) => {
        set({ loading: true, error: null }, false, 'voiceRecording/deleteAll');
        try {
          const resp = await fetch(`${API_BASE}/api/voice-recordings/all/${siblingPairId}`, {
            method: 'DELETE',
            headers: { 'x-parent-pin': parentPin },
          });
          if (!resp.ok) {
            const body = await resp.json().catch(() => ({}));
            set({ loading: false }, false, 'voiceRecording/deleteAll/fail');
            return { success: false, error: body.detail || 'Bulk delete failed' };
          }
          const result = await resp.json();
          set({ recordings: [], recordingCount: 0, loading: false }, false, 'voiceRecording/deleteAll/done');
          return { success: true, data: result };
        } catch (err) {
          set({ loading: false, error: err.message }, false, 'voiceRecording/deleteAll/error');
          return { success: false, error: err.message };
        }
      },

      setFilter: (filterKey, value) => {
        set(
          (state) => ({
            filters: { ...state.filters, [filterKey]: value || null },
          }),
          false,
          'voiceRecording/setFilter',
        );
      },

      setIsRecording: (recording) =>
        set({ isRecording: recording }, false, 'voiceRecording/setIsRecording'),

      fetchCommands: async (siblingPairId) => {
        if (!siblingPairId) return;
        try {
          const resp = await fetch(`${API_BASE}/api/voice-recordings/commands/${siblingPairId}`);
          if (resp.ok) {
            set({ commands: await resp.json() }, false, 'voiceRecording/fetchCommands');
          }
        } catch (err) {
          console.error('Failed to fetch voice commands:', err);
        }
      },

      getRecordingDetail: async (recordingId) => {
        try {
          const resp = await fetch(`${API_BASE}/api/voice-recordings/detail/${recordingId}`);
          if (!resp.ok) return null;
          return await resp.json();
        } catch (err) {
          console.error('Failed to fetch recording detail:', err);
          return null;
        }
      },

      reset: () =>
        set({
          recordings: [],
          isRecording: false,
          isUploading: false,
          recordingCount: 0,
          filters: { messageType: null, recorderName: null },
          loading: false,
          error: null,
          stats: null,
          commands: [],
        }, false, 'voiceRecording/reset'),
    }),
    { name: 'VoiceRecordingStore' },
  ),
);

import { create } from 'zustand';
import type { Language } from '@/i18n';

interface UIState {
  activeTab: string;
  language: Language;
  density: 'comfortable' | 'compact';
  preferencesHydrated: boolean;
  isSidebarOpen: boolean;
  isInspectorOpen: boolean;
  setActiveTab: (tab: string) => void;
  hydratePreferencesFromStorage: () => void;
  setLanguage: (language: Language) => void;
  setDensity: (density: 'comfortable' | 'compact') => void;
  toggleSidebar: () => void;
  toggleInspector: () => void;
  setSidebarOpen: (open: boolean) => void;
  setInspectorOpen: (open: boolean) => void;
}

const UI_LANGUAGE_KEY = 'aegis.ui.language';
const UI_DENSITY_KEY = 'aegis.ui.density';

function normalizeLanguage(value: string | null): Language {
  return value === 'tr' ? 'tr' : 'en';
}

function normalizeDensity(value: string | null): 'comfortable' | 'compact' {
  return value === 'compact' ? 'compact' : 'comfortable';
}

export const useUIStore = create<UIState>((set) => ({
  activeTab: 'Operator',
  language: 'en',
  density: 'comfortable',
  preferencesHydrated: false,
  isSidebarOpen: true,
  isInspectorOpen: false,
  setActiveTab: (tab) => set({ activeTab: tab }),
  hydratePreferencesFromStorage: () => {
    if (typeof window === 'undefined') return;

    try {
      set({
        language: normalizeLanguage(window.localStorage.getItem(UI_LANGUAGE_KEY)),
        density: normalizeDensity(window.localStorage.getItem(UI_DENSITY_KEY)),
        preferencesHydrated: true,
      });
    } catch {
      set({ preferencesHydrated: true });
    }
  },
  setLanguage: (language) => {
    if (typeof window !== 'undefined') {
      try {
        window.localStorage.setItem(UI_LANGUAGE_KEY, language);
      } catch {
        // Preference changes should still update UI if browser storage is unavailable.
      }
    }
    set({ language });
  },
  setDensity: (density) => {
    if (typeof window !== 'undefined') {
      try {
        window.localStorage.setItem(UI_DENSITY_KEY, density);
      } catch {
        // Preference changes should still update UI if browser storage is unavailable.
      }
    }
    set({ density });
  },
  toggleSidebar: () => set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),
  toggleInspector: () => set((state) => ({ isInspectorOpen: !state.isInspectorOpen })),
  setSidebarOpen: (isSidebarOpen) => set({ isSidebarOpen }),
  setInspectorOpen: (isInspectorOpen) => set({ isInspectorOpen }),
}));

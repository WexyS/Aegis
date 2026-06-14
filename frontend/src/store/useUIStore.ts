import { create } from 'zustand';
import type { Language } from '@/i18n';

interface UIState {
  activeTab: string;
  language: Language;
  density: 'comfortable' | 'compact';
  isSidebarOpen: boolean;
  isInspectorOpen: boolean;
  setActiveTab: (tab: string) => void;
  setLanguage: (language: Language) => void;
  setDensity: (density: 'comfortable' | 'compact') => void;
  toggleSidebar: () => void;
  toggleInspector: () => void;
}

const UI_LANGUAGE_KEY = 'aegis.ui.language';
const UI_DENSITY_KEY = 'aegis.ui.density';

function readLanguage(): Language {
  if (typeof window === 'undefined') return 'en';
  return window.localStorage.getItem(UI_LANGUAGE_KEY) === 'tr' ? 'tr' : 'en';
}

function readDensity(): 'comfortable' | 'compact' {
  if (typeof window === 'undefined') return 'comfortable';
  return window.localStorage.getItem(UI_DENSITY_KEY) === 'compact' ? 'compact' : 'comfortable';
}

export const useUIStore = create<UIState>((set) => ({
  activeTab: 'Mission',
  language: readLanguage(),
  density: readDensity(),
  isSidebarOpen: true,
  isInspectorOpen: true,
  setActiveTab: (tab) => set({ activeTab: tab }),
  setLanguage: (language) => {
    if (typeof window !== 'undefined') {
      window.localStorage.setItem(UI_LANGUAGE_KEY, language);
    }
    set({ language });
  },
  setDensity: (density) => {
    if (typeof window !== 'undefined') {
      window.localStorage.setItem(UI_DENSITY_KEY, density);
    }
    set({ density });
  },
  toggleSidebar: () => set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),
  toggleInspector: () => set((state) => ({ isInspectorOpen: !state.isInspectorOpen })),
}));

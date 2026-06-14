import { create } from 'zustand';

interface UIState {
  activeTab: string;
  isSidebarOpen: boolean;
  isInspectorOpen: boolean;
  setActiveTab: (tab: string) => void;
  toggleSidebar: () => void;
  toggleInspector: () => void;
}

export const useUIStore = create<UIState>((set) => ({
  activeTab: 'Mission',
  isSidebarOpen: true,
  isInspectorOpen: true,
  setActiveTab: (tab) => set({ activeTab: tab }),
  toggleSidebar: () => set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),
  toggleInspector: () => set((state) => ({ isInspectorOpen: !state.isInspectorOpen })),
}));

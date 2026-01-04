import { create } from 'zustand';
import { AuthStatus, User, AnalysisResult } from '../types';

interface AppState {
  authStatus: AuthStatus;
  user: User | null;
  analysisResult: AnalysisResult | null;
  isProcessing: boolean;
  
  setAuthStatus: (status: AuthStatus) => void;
  setUser: (user: User | null) => void;
  setAnalysisResult: (result: AnalysisResult | null) => void;
  setIsProcessing: (isProcessing: boolean) => void;
  logout: () => void;
}

export const useStore = create<AppState>((set) => ({
  authStatus: 'unauthenticated',
  user: null,
  analysisResult: null,
  isProcessing: false,

  setAuthStatus: (status) => set({ authStatus: status }),
  setUser: (user) => set({ user }),
  setAnalysisResult: (result) => set({ analysisResult: result }),
  setIsProcessing: (isProcessing) => set({ isProcessing }),
  logout: () => set({ authStatus: 'unauthenticated', user: null, analysisResult: null }),
}));

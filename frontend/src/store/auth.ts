'use client';

import { create } from 'zustand';
import { fetchCurrentUser, login, logout, register, updateOnboarding, User } from '@/lib/api';

interface AuthState {
  user: User | null;
  isLoading: boolean;
  loadCurrentUser: () => Promise<void>;
  signIn: (identifier: string, password: string) => Promise<User>;
  signUp: (input: { name: string; email: string; username?: string; password: string }) => Promise<User>;
  completeOnboarding: (input: { workflow_interest: string; team_size: string; experience_level: string }) => Promise<User>;
  signOut: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isLoading: true,
  loadCurrentUser: async () => {
    try {
      const user = await fetchCurrentUser();
      set({ user, isLoading: false });
    } catch {
      set({ user: null, isLoading: false });
    }
  },
  signIn: async (identifier, password) => {
    const user = await login({ identifier, password });
    set({ user, isLoading: false });
    return user;
  },
  signUp: async (input) => {
    const user = await register(input);
    set({ user, isLoading: false });
    return user;
  },
  completeOnboarding: async (input) => {
    const user = await updateOnboarding(input);
    set({ user });
    return user;
  },
  signOut: async () => {
    await logout();
    set({ user: null });
  },
}));

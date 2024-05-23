import { createContext } from 'preact';

export type InitialLoadingContextState = {
  startLoading: (id: string) => void;
  finishLoading: (id: string) => void;
};

export const InitialLoadingContext =
  createContext<InitialLoadingContextState | null>(null);

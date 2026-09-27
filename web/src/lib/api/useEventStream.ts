"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";
import { create } from "zustand";

import { invalidationKeysFor, parseLandmarkEvent } from "./stream";

export type StreamStatus = "connecting" | "live" | "error";

type StreamState = {
  status: StreamStatus;
  setStatus: (status: StreamStatus) => void;
};

export const useStreamStatus = create<StreamState>()((set) => ({
  status: "connecting",
  setStatus: (status) => set({ status }),
}));

/**
 * SSE kanalını bir kez açar; landmark geldikçe ilgili sorguları
 * tazeler. Bozuk yük atlanır, akış sürer; yeniden bağlanmayı
 * tarayıcı üstlenir (açılışta durum yine canlı olur).
 */
export function EventStreamLink() {
  const queryClient = useQueryClient();
  useEffect(() => {
    if (typeof window === "undefined" || typeof EventSource === "undefined") {
      return;
    }
    const { setStatus } = useStreamStatus.getState();
    setStatus("connecting");
    const source = new EventSource("/api/stream");
    source.onopen = () => setStatus("live");
    source.onerror = () => setStatus("error");
    const onLandmark = (event: MessageEvent) => {
      let keys;
      try {
        keys = invalidationKeysFor(parseLandmarkEvent(String(event.data)).kind);
      } catch {
        return;
      }
      for (const key of keys) {
        void queryClient.invalidateQueries({ queryKey: [...key] });
      }
      void queryClient.invalidateQueries({ queryKey: ["notifications-state"] });
    };
    source.addEventListener("landmark", onLandmark);
    return () => {
      source.close();
    };
  }, [queryClient]);
  return null;
}

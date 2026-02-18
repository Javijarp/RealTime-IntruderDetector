import { useCallback, useEffect, useState } from "react";
import { getDetectionEvents } from "../api/client";

export interface NewEventAlert {
  id: string;
  eventId: number;
  entityType: string;
  confidence: number;
  frameId?: number;
  timestamp: string;
  dismissed: boolean;
}

const VIEWED_EVENTS_KEY = "viewed_events";
const ALERTS_KEY = "event_alerts";

export const useNewEventNotifications = () => {
  const [alerts, setAlerts] = useState<NewEventAlert[]>([]);
  const [unviewedCount, setUnviewedCount] = useState(0);

  // Get viewed events from localStorage
  const getViewedEvents = useCallback(() => {
    try {
      const stored = localStorage.getItem(VIEWED_EVENTS_KEY);
      return stored ? JSON.parse(stored) : [];
    } catch {
      return [];
    }
  }, []);

  // Mark event as viewed
  const markEventAsViewed = useCallback(
    (eventId: number) => {
      const viewed = getViewedEvents();
      if (!viewed.includes(eventId)) {
        viewed.push(eventId);
        localStorage.setItem(VIEWED_EVENTS_KEY, JSON.stringify(viewed));
      }
      setUnviewedCount((prev) => Math.max(0, prev - 1));
    },
    [getViewedEvents],
  );

  // Dismiss an alert
  const dismissAlert = useCallback((alertId: string) => {
    setAlerts((prev) =>
      prev.map((a) => (a.id === alertId ? { ...a, dismissed: true } : a)),
    );
  }, []);

  // Clear all alerts
  const clearAllAlerts = useCallback(() => {
    setAlerts([]);
  }, []);

  // Check for new events
  const checkForNewEvents = useCallback(async () => {
    try {
      const response = await getDetectionEvents();
      const events = response.data || [];
      const viewed = getViewedEvents();

      // Find new unviewed events
      const newEvents = events.filter(
        (event: any) => !viewed.includes(event.id || event.eventId),
      );

      if (newEvents.length > 0) {
        const newAlerts = newEvents.map((event: any) => ({
          id: `alert_${event.id || event.eventId}_${Date.now()}`,
          eventId: event.id || event.eventId,
          entityType: event.entityType || event.entity_type,
          confidence: event.confidence,
          frameId: event.frameId,
          timestamp: event.timestamp || new Date().toISOString(),
          dismissed: false,
        }));

        setAlerts((prev) => [
          ...newAlerts,
          ...prev.filter((a) => !a.dismissed),
        ]);
        setUnviewedCount(newEvents.length);
      }
    } catch (error) {
      console.error("Error checking for new events:", error);
    }
  }, [getViewedEvents]);

  // Poll for new events every 5 seconds
  useEffect(() => {
    checkForNewEvents(); // Check immediately
    const interval = setInterval(checkForNewEvents, 5000);
    return () => clearInterval(interval);
  }, [checkForNewEvents]);

  return {
    alerts: alerts.filter((a) => !a.dismissed),
    dismissAlert,
    clearAllAlerts,
    markEventAsViewed,
    unviewedCount,
  };
};

import React from "react";
import { NewEventAlert } from "../hooks/useNewEventNotifications";
import "../styles/EventNotificationPanel.css";

interface EventNotificationPanelProps {
  alerts: NewEventAlert[];
  onDismiss: (alertId: string) => void;
  onEventClick: (eventId: number) => void;
}

const EventNotificationPanel: React.FC<EventNotificationPanelProps> = ({
  alerts,
  onDismiss,
  onEventClick,
}) => {
  if (alerts.length === 0) return null;

  return (
    <div className="event-notification-panel">
      <div className="notification-header">
        <h3 className="text-sm font-semibold text-gray-800">
          🔔 New Events ({alerts.length})
        </h3>
      </div>
      <div className="notification-list">
        {alerts.map((alert) => (
          <div
            key={alert.id}
            className="notification-item"
            onClick={() => onEventClick(alert.eventId)}>
            <div className="notification-content">
              <div className="notification-title">
                <span className="entity-badge">{alert.entityType}</span>
                <span className="confidence-badge">
                  {(alert.confidence * 100).toFixed(1)}%
                </span>
              </div>
              <div className="notification-time">
                {new Date(alert.timestamp).toLocaleTimeString()}
              </div>
            </div>
            <button
              className="notification-dismiss"
              onClick={(e) => {
                e.stopPropagation();
                onDismiss(alert.id);
              }}
              aria-label="Dismiss notification">
              ✕
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};

export default EventNotificationPanel;

import { AlertCircle, CheckCircle, Info, X } from "lucide-react";
import React, { useEffect } from "react";

export const AlertContext = React.createContext();

export function AlertProvider({ children }) {
  const [alerts, setAlerts] = React.useState([]);

  const addAlert = (message, type = "info", duration = 5000) => {
    const id = Date.now();
    const alert = { id, message, type };

    setAlerts((prev) => [...prev, alert]);

    if (duration > 0) {
      setTimeout(() => {
        removeAlert(id);
      }, duration);
    }

    return id;
  };

  const removeAlert = (id) => {
    setAlerts((prev) => prev.filter((alert) => alert.id !== id));
  };

  return (
    <AlertContext.Provider value={{ addAlert, removeAlert, alerts }}>
      {children}
      <AlertContainer alerts={alerts} onRemove={removeAlert} />
    </AlertContext.Provider>
  );
}

export function useAlert() {
  const context = React.useContext(AlertContext);
  if (!context) {
    throw new Error("useAlert must be used within AlertProvider");
  }
  return context;
}

function AlertContainer({ alerts, onRemove }) {
  return (
    <div className="fixed bottom-4 right-4 space-y-2 z-50">
      {alerts.map((alert) => (
        <Alert
          key={alert.id}
          alert={alert}
          onClose={() => onRemove(alert.id)}
        />
      ))}
    </div>
  );
}

function Alert({ alert, onClose }) {
  const bgColor = {
    success: "bg-green-50 border-green-200",
    error: "bg-red-50 border-red-200",
    warning: "bg-yellow-50 border-yellow-200",
    info: "bg-blue-50 border-blue-200",
  }[alert.type];

  const textColor = {
    success: "text-green-800",
    error: "text-red-800",
    warning: "text-yellow-800",
    info: "text-blue-800",
  }[alert.type];

  const iconColor = {
    success: "text-green-500",
    error: "text-red-500",
    warning: "text-yellow-500",
    info: "text-blue-500",
  }[alert.type];

  const Icon = {
    success: CheckCircle,
    error: AlertCircle,
    warning: AlertCircle,
    info: Info,
  }[alert.type];

  return (
    <div
      className={`${bgColor} border rounded-lg p-4 flex items-start gap-3 max-w-md animate-in fade-in slide-in-from-right-4 duration-300`}>
      <Icon className={`${iconColor} h-5 w-5 flex-shrink-0 mt-0.5`} />
      <p className={`${textColor} text-sm font-medium flex-1`}>
        {alert.message}
      </p>
      <button
        onClick={onClose}
        className="text-gray-400 hover:text-gray-600 flex-shrink-0">
        <X className="h-4 w-4" />
      </button>
    </div>
  );
}

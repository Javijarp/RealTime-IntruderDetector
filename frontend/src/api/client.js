import axios from "axios";

// Use relative API path which works both locally and in Docker
const API_BASE_URL = "";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Detection Events
export const getDetectionEvents = () => api.get("/events");
export const getDetectionEventById = (id) => api.get(`/events/${id}`);
export const createDetectionEvent = (data) => api.post("/events", data);
export const updateDetectionEvent = (id, data) =>
  api.patch(`/events/${id}`, data);
export const markEventAsProcessed = (id) =>
  api.patch(`/events/${id}/process`);

// Frames
export const getFrames = () => api.get("/frames");
export const getFrameById = (id) => api.get(`/frames/${id}`);
export const createFrame = (formData) =>
  api.post("/frames", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });

export default api;

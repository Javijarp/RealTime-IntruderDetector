import axios from 'axios';

export interface DetectionEvent {
    id: number;
    eventId?: number;
    entity_type: string;
    confidence: number;
    frameId?: number;
    timestamp?: string;
    processed?: boolean;
}

export interface Frame {
    id: number;
    frameNumber: number;
    imageData: string | null; // Base64 encoded image
    imageType: string;
    imagePath?: string;
    timestamp: string;
    createdAt?: string;
    detectionEvent?: DetectionEvent;
}

// Use relative API path which works both locally and in Docker via nginx proxy
const API_BASE_URL = '';
const EVENTS_URL = `${API_BASE_URL}/api/events`;
const FRAMES_URL = `${API_BASE_URL}/api/frames`;

export const fetchEvents = async (): Promise<DetectionEvent[]> => {
    try {
        const response = await axios.get<DetectionEvent[]>(EVENTS_URL);
        return response.data || [];
    } catch (error) {
        console.error('Error fetching events:', error);
        return [];
    }
};

export const fetchFrames = async (): Promise<Frame[]> => {
    try {
        const response = await axios.get<Frame[]>(FRAMES_URL);
        return response.data || [];
    } catch (error) {
        console.error('Error fetching frames:', error);
        return [];
    }
};

export const getFrameById = async (frameId: number): Promise<Frame | null> => {
    try {
        const response = await axios.get<Frame>(`${FRAMES_URL}/${frameId}`);
        return response.data;
    } catch (error) {
        console.error(`Error fetching frame ${frameId}:`, error);
        return null;
    }
};

export const createEvent = async (eventData: DetectionEvent): Promise<any> => {
    try {
        const response = await axios.post(EVENTS_URL, eventData);
        return response.data;
    } catch (error) {
        console.error('Error creating event:', error);
        throw error;
    }
};
import axios from 'axios';

const API_BASE = '/api';

const api = axios.create({
    baseURL: API_BASE,
    timeout: 60000, // 60s timeout for AI operations
});

// Request interceptor for logging
api.interceptors.request.use(
    (config) => {
        console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`);
        return config;
    },
    (error) => Promise.reject(error)
);

// Response interceptor for error handling
api.interceptors.response.use(
    (response) => response,
    (error) => {
        const message = error.response?.data?.detail || error.message || 'An error occurred';
        console.error('[API Error]', message);
        return Promise.reject(new Error(message));
    }
);

export const pixllApi = {
    // Health check
    health: () => api.get('/health'),

    // Upload
    upload: async (file) => {
        const formData = new FormData();
        formData.append('file', file);
        return api.post('/upload', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
    },

    // Session
    getSession: (sessionId) => api.get(`/sessions/${sessionId}`),
    deleteSession: (sessionId) => api.delete(`/sessions/${sessionId}`),

    // Cleaning
    cleanData: (sessionId) => api.post(`/clean/${sessionId}`),
    getCleaningReport: (sessionId) => api.get(`/clean/${sessionId}/report`),
    getData: (sessionId, cleaned = true, page = 1, pageSize = 50) =>
        api.get(`/data/${sessionId}`, { params: { cleaned, page, page_size: pageSize } }),

    // Export
    exportData: (sessionId, format, cleaned = true) =>
        api.get(`/export/${sessionId}/${format}`, {
            params: { cleaned },
            responseType: 'blob',
        }),

    // Visualization
    visualize: (sessionId, query, chartTypeOverride = null) =>
        api.post('/visualize', {
            session_id: sessionId,
            query,
            chart_type_override: chartTypeOverride,
        }),

    overrideChartType: (sessionId, chartType) =>
        api.post('/visualize/override', null, {
            params: { session_id: sessionId, chart_type: chartType },
        }),

    exportChart: (sessionId, format) =>
        api.get(`/visualize/${sessionId}/export/${format}`, {
            responseType: 'blob',
        }),

    getColumns: (sessionId) => api.get(`/visualize/${sessionId}/columns`),
};

export default api;

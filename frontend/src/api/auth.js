import api from './axios'

export const authAPI = {
    signup: (data) => api.post('/auth/signup', data),

    login: (data) => api.post('/auth/login', data),

    refresh: () => api.post('/auth/refresh'),

    me: () => api.get('/auth/me'),

    logout: () => api.post('/auth/logout'),
}

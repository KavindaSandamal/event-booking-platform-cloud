import { configureStore } from '@reduxjs/toolkit';
import authReducer from './authSlice';

// Custom middleware for token management
const tokenMiddleware = (store) => (next) => (action) => {
    const result = next(action);

    // Check if user is authenticated and token is about to expire
    const state = store.getState();
    const { token, refreshToken, tokenExpiry, isAuthenticated } = state.auth;

    if (isAuthenticated && token && refreshToken && tokenExpiry) {
        const timeUntilExpiry = tokenExpiry - Date.now();
        const fiveMinutes = 5 * 60 * 1000; // 5 minutes in milliseconds

        // If token expires in less than 5 minutes, refresh it
        if (timeUntilExpiry < fiveMinutes && timeUntilExpiry > 0) {
            store.dispatch({ type: 'auth/refreshToken', payload: refreshToken });
        }

        // If token is expired, logout
        if (timeUntilExpiry <= 0) {
            store.dispatch({ type: 'auth/logout' });
        }
    }

    return result;
};

// Activity tracking middleware
const activityMiddleware = (store) => (next) => (action) => {
    const result = next(action);

    // Update last activity on user interactions
    if (action.type !== 'auth/updateLastActivity' &&
        action.type !== 'auth/setLoading' &&
        action.type !== 'auth/clearError') {
        store.dispatch({ type: 'auth/updateLastActivity' });
    }

    return result;
};

export const store = configureStore({
    reducer: {
        auth: authReducer,
    },
    middleware: (getDefaultMiddleware) =>
        getDefaultMiddleware().concat(tokenMiddleware, activityMiddleware),
}); 
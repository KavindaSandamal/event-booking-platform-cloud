import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axios from 'axios';

// Async thunk for token refresh
export const refreshToken = createAsyncThunk(
    'auth/refreshToken',
    async (refreshTokenValue, { rejectWithValue }) => {
        try {
            const response = await axios.post('http://localhost:8001/refresh', {
                refresh_token: refreshTokenValue
            });
            return response.data;
        } catch (error) {
            return rejectWithValue(error.response?.data?.detail || 'Token refresh failed');
        }
    }
);

// Async thunk for token verification
export const verifyToken = createAsyncThunk(
    'auth/verifyToken',
    async (token, { rejectWithValue }) => {
        try {
            const response = await axios.post('http://localhost:8001/verify', {
                token: token
            });
            return response.data;
        } catch (error) {
            return rejectWithValue(error.response?.data?.detail || 'Token verification failed');
        }
    }
);

// Helper function to get stored tokens
const getStoredTokens = () => {
    const token = localStorage.getItem('token');
    const refreshToken = localStorage.getItem('refreshToken');
    const tokenExpiry = localStorage.getItem('tokenExpiry');
    const user = localStorage.getItem('user');
    
    return {
        token,
        refreshToken,
        tokenExpiry: tokenExpiry ? parseInt(tokenExpiry) : null,
        user: user ? JSON.parse(user) : null
    };
};

// Helper function to check if token is expired
const isTokenExpired = (expiry) => {
    if (!expiry) return true;
    return Date.now() >= expiry;
};

// Helper function to calculate token expiry time
const calculateTokenExpiry = (expiresIn) => {
    return Date.now() + (expiresIn * 1000);
};

const initialState = {
    ...getStoredTokens(),
    isAuthenticated: false,
    isLoading: false,
    error: null,
    lastActivity: Date.now(),
    autoLogoutTimer: null
};

const authSlice = createSlice({
    name: 'auth',
    initialState,
    reducers: {
        setCredentials: (state, action) => {
            const { access_token, refresh_token, expires_in, user } = action.payload;
            state.token = access_token;
            state.refreshToken = refresh_token;
            state.tokenExpiry = calculateTokenExpiry(expires_in);
            state.user = user;
            state.isAuthenticated = true;
            state.error = null;
            state.lastActivity = Date.now();
            
            // Store in localStorage
            localStorage.setItem('token', access_token);
            localStorage.setItem('refreshToken', refresh_token);
            localStorage.setItem('tokenExpiry', state.tokenExpiry.toString());
            if (user) {
                localStorage.setItem('user', JSON.stringify(user));
            }
            
            // Set up auto logout timer
            state.autoLogoutTimer = setTimeout(() => {
                // This will be handled by the middleware
            }, expires_in * 1000);
        },
        
        logout: (state) => {
            state.token = null;
            state.refreshToken = null;
            state.tokenExpiry = null;
            state.user = null;
            state.isAuthenticated = false;
            state.error = null;
            state.lastActivity = null;
            
            // Clear localStorage
            localStorage.removeItem('token');
            localStorage.removeItem('refreshToken');
            localStorage.removeItem('tokenExpiry');
            localStorage.removeItem('user');
            
            // Clear auto logout timer
            if (state.autoLogoutTimer) {
                clearTimeout(state.autoLogoutTimer);
                state.autoLogoutTimer = null;
            }
        },
        
        updateUser: (state, action) => {
            state.user = action.payload;
            localStorage.setItem('user', JSON.stringify(action.payload));
        },
        
        updateLastActivity: (state) => {
            state.lastActivity = Date.now();
        },
        
        setError: (state, action) => {
            state.error = action.payload;
        },
        
        clearError: (state) => {
            state.error = null;
        },
        
        setLoading: (state, action) => {
            state.isLoading = action.payload;
        }
    },
    
    extraReducers: (builder) => {
        builder
            .addCase(refreshToken.pending, (state) => {
                state.isLoading = true;
                state.error = null;
            })
            .addCase(refreshToken.fulfilled, (state, action) => {
                const { access_token, refresh_token, expires_in } = action.payload;
                state.token = access_token;
                state.refreshToken = refresh_token;
                state.tokenExpiry = calculateTokenExpiry(expires_in);
                state.isLoading = false;
                state.error = null;
                state.lastActivity = Date.now();
                
                // Update localStorage
                localStorage.setItem('token', access_token);
                localStorage.setItem('refreshToken', refresh_token);
                localStorage.setItem('tokenExpiry', state.tokenExpiry.toString());
            })
            .addCase(refreshToken.rejected, (state, action) => {
                state.isLoading = false;
                state.error = action.payload;
                // If refresh fails, logout
                authSlice.caseReducers.logout(state);
            })
            .addCase(verifyToken.pending, (state) => {
                state.isLoading = true;
                state.error = null;
            })
            .addCase(verifyToken.fulfilled, (state, action) => {
                state.isLoading = false;
                state.error = null;
                state.lastActivity = Date.now();
            })
            .addCase(verifyToken.rejected, (state, action) => {
                state.isLoading = false;
                state.error = action.payload;
                // If verification fails, logout
                authSlice.caseReducers.logout(state);
            });
    }
});

export const { 
    setCredentials, 
    logout, 
    updateUser, 
    updateLastActivity, 
    setError, 
    clearError, 
    setLoading 
} = authSlice.actions;

export default authSlice.reducer;

// Selectors
export const selectCurrentUser = (state) => state.auth.user;
export const selectIsAuthenticated = (state) => state.auth.isAuthenticated;
export const selectToken = (state) => state.auth.token;
export const selectRefreshToken = (state) => state.auth.refreshToken;
export const selectTokenExpiry = (state) => state.auth.tokenExpiry;
export const selectIsLoading = (state) => state.auth.isLoading;
export const selectError = (state) => state.auth.error;
export const selectLastActivity = (state) => state.auth.lastActivity;

// Utility selectors
export const selectIsTokenExpired = (state) => {
    const expiry = state.auth.tokenExpiry;
    return isTokenExpired(expiry);
};

export const selectTimeUntilExpiry = (state) => {
    const expiry = state.auth.tokenExpiry;
    if (!expiry) return 0;
    return Math.max(0, expiry - Date.now());
}; 
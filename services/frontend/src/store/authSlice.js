// authSlice.js
import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import axios from "axios";

// ✅ Async thunk for refreshing token
export const refreshToken = createAsyncThunk(
  "auth/refreshToken",
  async (refreshToken, { rejectWithValue }) => {
    try {
      const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://event-booking-platform-alb-50648091.us-west-2.elb.amazonaws.com';
      const response = await axios.post(
        `${baseURL}/auth/refresh`,
        { refresh_token: refreshToken }
      );
      return response.data;
    } catch (err) {
      return rejectWithValue(err.response?.data || "Token refresh failed");
    }
  }
);

// ✅ Async thunk for token verification
export const verifyToken = createAsyncThunk(
  "auth/verifyToken",
  async (token, { rejectWithValue }) => {
    try {
      const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://event-booking-platform-alb-50648091.us-west-2.elb.amazonaws.com';
      const response = await axios.post(
        `${baseURL}/auth/verify`,
        { token }
      );
      return response.data;
    } catch (err) {
      return rejectWithValue(err.response?.data || "Token verification failed");
    }
  }
);

// Load initial state from localStorage
const loadInitialState = () => {
  try {
    const authData = localStorage.getItem('auth');
    if (authData) {
      const parsed = JSON.parse(authData);
      return {
        token: parsed.token || null,
        refreshToken: parsed.refreshToken || null,
        tokenExpiry: parsed.tokenExpiry || null,
        user: parsed.user || null,
        isAuthenticated: !!(parsed.token && parsed.tokenExpiry && parsed.tokenExpiry > Date.now()),
        lastActivity: Date.now(),
        loading: false,
        error: null,
      };
    }
  } catch (e) {
    // Invalid JSON, use default state
  }
  
  return {
    token: null,
    refreshToken: null,
    tokenExpiry: null,
    user: null,
    isAuthenticated: false,
    lastActivity: Date.now(),
    loading: false,
    error: null,
  };
};

const initialState = loadInitialState();

// ✅ Slice
const authSlice = createSlice({
  name: "auth",
  initialState,
  reducers: {
    setCredentials: (state, action) => {
      const { token, refreshToken, expiresIn, user } = action.payload;

      state.token = token;
      state.refreshToken = refreshToken;
      state.user = user;
      state.isAuthenticated = true;

      // Convert `expiresIn` (seconds) → absolute timestamp in ms
      if (expiresIn) {
        state.tokenExpiry = Date.now() + expiresIn * 1000;
      }

      // Persist auth to localStorage
      localStorage.setItem(
        "auth",
        JSON.stringify({
          token,
          refreshToken,
          tokenExpiry: state.tokenExpiry,
          user,
        })
      );
    },
    logout: (state) => {
      state.token = null;
      state.refreshToken = null;
      state.tokenExpiry = null;
      state.user = null;
      state.isAuthenticated = false;
      localStorage.removeItem("auth");
    },
    updateLastActivity: (state) => {
      state.lastActivity = Date.now();
    },
    setLoading: (state, action) => {
      state.loading = action.payload;
    },
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(refreshToken.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(refreshToken.fulfilled, (state, action) => {
        const { token, refreshToken, expiresIn, user } = action.payload;

        state.token = token;
        state.refreshToken = refreshToken;
        state.user = user;
        state.isAuthenticated = true;

        // Same expiry conversion
        if (expiresIn) {
          state.tokenExpiry = Date.now() + expiresIn * 1000;
        }

        localStorage.setItem(
          "auth",
          JSON.stringify({
            token,
            refreshToken,
            tokenExpiry: state.tokenExpiry,
            user,
          })
        );

        state.loading = false;
      })
      .addCase(refreshToken.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload || "Failed to refresh token";
      })
      .addCase(verifyToken.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(verifyToken.fulfilled, (state) => {
        state.loading = false;
        state.error = null;
        state.lastActivity = Date.now();
      })
      .addCase(verifyToken.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload || "Token verification failed";
        // If verification fails, logout
        authSlice.caseReducers.logout(state);
      });
  },
});

export const { setCredentials, logout, updateLastActivity, setLoading, clearError } =
  authSlice.actions;

export default authSlice.reducer;

// Selectors
export const selectToken = (state) => state.auth.token;
export const selectRefreshToken = (state) => state.auth.refreshToken;
export const selectIsAuthenticated = (state) => state.auth.isAuthenticated;
export const selectUser = (state) => state.auth.user;
export const selectLoading = (state) => state.auth.loading;
export const selectError = (state) => state.auth.error;
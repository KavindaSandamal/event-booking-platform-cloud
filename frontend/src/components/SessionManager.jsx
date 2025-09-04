import React, { useEffect, useRef } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import {
    selectIsAuthenticated,
    selectToken,
    selectRefreshToken,
    logout,
    refreshToken,
    verifyToken
} from '../store/authSlice';

const SessionManager = () => {
    const dispatch = useDispatch();
    const isAuthenticated = useSelector(selectIsAuthenticated);
    const token = useSelector(selectToken);
    const refreshTokenValue = useSelector(selectRefreshToken);

    const inactivityTimerRef = useRef(null);
    const tokenCheckTimerRef = useRef(null);

    // Inactivity timeout (30 minutes)
    const INACTIVITY_TIMEOUT = 30 * 60 * 1000;
    // Token check interval (1 minute)
    const TOKEN_CHECK_INTERVAL = 60 * 1000;

    // Handle user activity
    const handleUserActivity = () => {
        if (inactivityTimerRef.current) {
            clearTimeout(inactivityTimerRef.current);
        }

        if (isAuthenticated) {
            inactivityTimerRef.current = setTimeout(() => {
                console.log('User inactive for 30 minutes, logging out...');
                dispatch(logout());
            }, INACTIVITY_TIMEOUT);
        }
    };

    // Check token validity
    const checkTokenValidity = async () => {
        if (!isAuthenticated || !token) return;

        try {
            await dispatch(verifyToken(token)).unwrap();
        } catch {
            console.log('Token verification failed, attempting refresh...');
            if (refreshTokenValue) {
                try {
                    await dispatch(refreshToken(refreshTokenValue)).unwrap();
                } catch {
                    console.log('Token refresh failed, logging out...');
                    dispatch(logout());
                }
            } else {
                dispatch(logout());
            }
        }
    };

    // Listen for user activity
    useEffect(() => {
        const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click'];

        events.forEach(event => {
            document.addEventListener(event, handleUserActivity, true);
        });

        return () => {
            events.forEach(event => {
                document.removeEventListener(event, handleUserActivity, true);
            });
        };
    }, [isAuthenticated]);

    // Set up token check loop
    useEffect(() => {
        if (isAuthenticated && token) {
            checkTokenValidity();
            tokenCheckTimerRef.current = setInterval(checkTokenValidity, TOKEN_CHECK_INTERVAL);
        }

        return () => {
            if (tokenCheckTimerRef.current) {
                clearInterval(tokenCheckTimerRef.current);
            }
        };
    }, [isAuthenticated, token, refreshTokenValue]);

    // Clean up timers
    useEffect(() => {
        return () => {
            if (inactivityTimerRef.current) clearTimeout(inactivityTimerRef.current);
            if (tokenCheckTimerRef.current) clearInterval(tokenCheckTimerRef.current);
        };
    }, []);

    return null;
};

export default SessionManager;

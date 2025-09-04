# JWT Authentication & Session Management

This document describes the enhanced JWT authentication and session management features implemented in the Event Booking Platform.

## 🔐 JWT Security Features

### Secure JWT Secret Generation
- **Auto-generation**: If no JWT secret is provided in environment variables, a secure 32-byte random secret is automatically generated
- **Environment Configuration**: JWT secret can be set via `JWT_SECRET` environment variable
- **Production Ready**: Uses `secrets.token_urlsafe()` for cryptographically secure random generation

### Token Types
- **Access Token**: Short-lived (30 minutes) for API authentication
- **Refresh Token**: Long-lived (7 days) for token renewal
- **Token Validation**: Includes token type verification to prevent misuse

### Enhanced Token Payload
```json
{
  "sub": "user_id",
  "exp": "expiration_timestamp",
  "iat": "issued_at_timestamp",
  "type": "access|refresh"
}
```

## ⏰ Automatic Session Management

### Token Expiration
- **Access Token**: 30 minutes (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`)
- **Refresh Token**: 7 days (configurable via `REFRESH_TOKEN_EXPIRE_DAYS`)
- **Automatic Refresh**: Tokens are refreshed 5 minutes before expiration

### Inactivity Timeout
- **30-minute inactivity**: Users are automatically logged out after 30 minutes of inactivity
- **Activity Tracking**: Monitors mouse, keyboard, scroll, and touch events
- **Real-time Updates**: Session status updates in real-time

### Automatic Logout Scenarios
1. **Token Expiration**: When access token expires and refresh fails
2. **Inactivity**: After 30 minutes of user inactivity
3. **Invalid Token**: When token verification fails
4. **Refresh Failure**: When refresh token is invalid or expired

## 🔄 Redux State Management

### Enhanced Auth Slice
```javascript
{
  token: "access_token",
  refreshToken: "refresh_token", 
  tokenExpiry: "expiration_timestamp",
  user: { email: "user@example.com" },
  isAuthenticated: true,
  isLoading: false,
  error: null,
  lastActivity: "timestamp",
  autoLogoutTimer: "timer_reference"
}
```

### Async Actions
- `refreshToken()`: Automatically refresh expired tokens
- `verifyToken()`: Validate token authenticity and expiration
- `setCredentials()`: Store new tokens with expiration tracking
- `logout()`: Clear all session data and timers

### Selectors
- `selectIsTokenExpired()`: Check if current token is expired
- `selectTimeUntilExpiry()`: Get time remaining until token expires
- `selectLastActivity()`: Get timestamp of last user activity

## 🛡️ API Security

### Axios Interceptors
- **Request Interceptor**: Automatically adds Authorization header with current token
- **Response Interceptor**: Handles 401 errors by attempting token refresh
- **Automatic Retry**: Failed requests are retried with new tokens after refresh

### Service-Specific APIs
- `authAPI`: Authentication endpoints
- `catalogAPI`: Event catalog endpoints  
- `bookingAPI`: Booking management endpoints
- `paymentAPI`: Payment processing endpoints

## 🎯 Session Monitoring

### Development Mode Features
- **Session Info Display**: Shows token expiration countdown and last activity
- **Real-time Updates**: Live session status in top-right corner
- **Debug Information**: Token expiry time and activity timestamps

### Production Features
- **Silent Monitoring**: Background session management without UI indicators
- **Error Logging**: Comprehensive error logging for session issues
- **Performance Optimized**: Minimal overhead for production use

## 🔧 Configuration

### Environment Variables
```bash
# JWT Configuration
JWT_SECRET=                    # Leave empty for auto-generation
JWT_ALGORITHM=HS256           # Token signing algorithm
ACCESS_TOKEN_EXPIRE_MINUTES=30 # Access token lifetime
REFRESH_TOKEN_EXPIRE_DAYS=7   # Refresh token lifetime
```

### Backend Endpoints
- `POST /login`: User authentication with token generation
- `POST /register`: User registration with token generation
- `POST /refresh`: Token refresh endpoint
- `POST /verify`: Token validation endpoint
- `POST /logout`: Session termination endpoint

## 🚀 Usage Examples

### Login Flow
```javascript
// Login automatically handles token storage and session setup
const response = await authAPI.post('/login', { email, password });
// Tokens are automatically stored and session timers are set
```

### Automatic Token Refresh
```javascript
// No manual intervention needed - handled by interceptors
const bookings = await bookingAPI.get('/my-bookings');
// If token expires, it's automatically refreshed and request retried
```

### Session Monitoring
```javascript
// SessionManager component handles all session monitoring
<SessionManager />
// Automatically manages logout, refresh, and activity tracking
```

## 🔒 Security Best Practices

1. **Secure Secret Generation**: Uses cryptographically secure random generation
2. **Token Type Validation**: Prevents access token misuse as refresh token
3. **Automatic Expiration**: Short-lived access tokens reduce attack window
4. **Activity Monitoring**: Prevents session hijacking through inactivity
5. **Secure Storage**: Tokens stored in localStorage with expiration tracking
6. **Automatic Cleanup**: All session data cleared on logout

## 🐛 Troubleshooting

### Common Issues
1. **Token Expired**: Check if system time is synchronized
2. **Refresh Failed**: Verify refresh token hasn't expired
3. **Inactivity Logout**: Check if user activity events are being captured
4. **API Errors**: Ensure all services are running and accessible

### Debug Information
- Check browser console for session-related logs
- Monitor network requests for token refresh attempts
- Verify localStorage contains valid tokens and expiration times

## 📝 Migration Notes

### From Previous Version
- Update environment variables to include new JWT settings
- Ensure all components use new API utilities instead of direct axios calls
- Add SessionManager component to main App component
- Update Redux store configuration to include new middleware

### Breaking Changes
- Token response format changed to include refresh tokens
- Authentication state structure updated with new fields
- API calls now use service-specific axios instances with interceptors

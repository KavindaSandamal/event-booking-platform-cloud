# Frontend Environment Configuration Guide

## Overview
This guide explains how to configure the frontend environment variables for different deployment scenarios.

## Environment Variables

### Required Variables

#### `VITE_API_BASE_URL`
The base URL for your backend API services.

**Options:**
- **Local Development**: `http://localhost:8000`
- **Production (AWS)**: `http://event-booking-platform-alb-50648091.us-west-2.elb.amazonaws.com`
- **Custom Domain**: `https://your-domain.com`

### Optional Variables

#### Application Configuration
```bash
VITE_APP_NAME=Event Booking Platform
VITE_APP_VERSION=1.0.0
```

#### Feature Flags
```bash
VITE_ENABLE_ANALYTICS=false
VITE_ENABLE_DEBUG=true
```

#### Development Settings
```bash
VITE_DEV_MODE=true
VITE_MOCK_API=false
```

## Configuration Examples

### 1. Local Development
```bash
# .env file for local development
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_NAME=Event Booking Platform (Dev)
VITE_ENABLE_DEBUG=true
VITE_DEV_MODE=true
```

### 2. Production (AWS)
```bash
# .env file for production
VITE_API_BASE_URL=http://event-booking-platform-alb-50648091.us-west-2.elb.amazonaws.com
VITE_APP_NAME=Event Booking Platform
VITE_ENABLE_DEBUG=false
VITE_DEV_MODE=false
```

### 3. Custom Domain
```bash
# .env file for custom domain
VITE_API_BASE_URL=https://api.your-domain.com
VITE_APP_NAME=Event Booking Platform
VITE_ENABLE_DEBUG=false
VITE_DEV_MODE=false
```

## How to Update

### Method 1: Edit .env File
1. Open your `.env` file
2. Update the `VITE_API_BASE_URL` line:
   ```bash
   VITE_API_BASE_URL=http://event-booking-platform-alb-50648091.us-west-2.elb.amazonaws.com
   ```

### Method 2: Environment-Specific Files
Create different `.env` files for different environments:
- `.env.local` - Local development
- `.env.production` - Production deployment
- `.env.staging` - Staging environment

### Method 3: Build-Time Configuration
Set environment variables during build:
```bash
# For production build
VITE_API_BASE_URL=http://event-booking-platform-alb-50648091.us-west-2.elb.amazonaws.com npm run build

# For development
VITE_API_BASE_URL=http://localhost:8000 npm run dev
```

## Current AWS Load Balancer URL
```
http://event-booking-platform-alb-50648091.us-west-2.elb.amazonaws.com
```

## Testing the Configuration

### 1. Check Environment Variables
```javascript
// In your frontend code
console.log('API Base URL:', import.meta.env.VITE_API_BASE_URL);
```

### 2. Test API Connection
```javascript
// Test if the API is reachable
fetch(`${import.meta.env.VITE_API_BASE_URL}/health`)
  .then(response => response.json())
  .then(data => console.log('API Health:', data))
  .catch(error => console.error('API Error:', error));
```

## Troubleshooting

### Common Issues

1. **CORS Errors**
   - Ensure your backend allows requests from your frontend domain
   - Check if the API URL is correct

2. **Environment Variables Not Loading**
   - Make sure variables start with `VITE_`
   - Restart your development server after changing `.env`

3. **API Not Reachable**
   - Verify the Load Balancer URL is correct
   - Check if the backend services are running
   - Ensure security groups allow HTTP traffic

### Debug Commands
```bash
# Check if environment variables are loaded
npm run dev

# Check build output
npm run build

# Test API connectivity
curl http://event-booking-platform-alb-50648091.us-west-2.elb.amazonaws.com/health
```

## Security Considerations

1. **Never commit sensitive data** to version control
2. **Use HTTPS** in production
3. **Validate environment variables** before use
4. **Use different URLs** for different environments

## Next Steps

1. Update your `.env` file with the correct `VITE_API_BASE_URL`
2. Test the frontend with the new configuration
3. Deploy the updated frontend to your hosting platform
4. Monitor the application for any connectivity issues

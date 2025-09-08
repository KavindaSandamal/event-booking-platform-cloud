FROM nginx:alpine

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Create a simple index.html if no static files exist
RUN echo '<html><body><h1>Event Booking Platform</h1><p>API Gateway is running</p></body></html>' > /usr/share/nginx/html/index.html

# Expose port 80
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]

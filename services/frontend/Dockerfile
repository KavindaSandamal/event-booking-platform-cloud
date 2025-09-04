FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Build the production version
RUN npm run build

# Install serve to serve the built files
RUN npm install -g serve

# Expose port 3000
EXPOSE 3000

# Serve the production build
CMD ["serve", "-s", "dist", "-l", "3000"]

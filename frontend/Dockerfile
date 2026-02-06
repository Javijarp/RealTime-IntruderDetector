# Stage 1: Build the React frontend
FROM node:18-alpine as build

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* yarn.lock* ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Build the application with OpenSSL legacy provider for Node 18 compatibility
RUN NODE_OPTIONS=--openssl-legacy-provider npm run build

# Stage 2: Serve with Nginx
FROM nginx:alpine

WORKDIR /usr/share/nginx/html

# Remove default config
RUN rm -rf /etc/nginx/conf.d/default.conf

# Copy nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built app from build stage
COPY --from=build /app/build .

EXPOSE 3000

CMD ["nginx", "-g", "daemon off;"]

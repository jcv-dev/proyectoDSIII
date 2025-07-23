## Dockerfile
################################
## BUILD ENVIRONMENT ###########
################################

# Use the official Node.js Alpine image (adjust based on your project's requirements)
FROM node:20-alpine3.20 As build

# Set the working directory inside the container
WORKDIR /usr/src/app

# Copy package.json and package-lock.json into the container
# Add a build argument to force cache invalidation for this layer
ARG CACHE_BUSTER_PKG=$(date +%s)
COPY package*.json package-lock.json ./

# Install dependencies using npm
RUN npm ci

# Copy the project files into the working directory
# Add a build argument to force cache invalidation for this layer
ARG CACHE_BUSTER_SRC=$(date +%s)
COPY ./ ./

# Build the React app for production
RUN npm run build

################################
#### PRODUCTION ENVIRONMENT ####
################################

# Use the official NGINX image for production
FROM nginx:stable-alpine as production

# Copy nginx configuration into the Nginx conf.d directory, explicitly naming it default.conf.
# This ensures Nginx picks up your configuration correctly.
# Add a build argument to force cache invalidation for this layer
ARG CACHE_BUSTER_NGINX=$(date +%s)
COPY --from=build /usr/src/app/nginx.conf /etc/nginx/conf.d/default.conf

# Copy the build output from the dist folder into the Nginx html directory.
# Add a build argument to force cache invalidation for this layer
ARG CACHE_BUSTER_DIST=$(date +%s)
COPY --from=build /usr/src/app/dist /usr/share/nginx/html

# Expose port 80 to allow access to the app
EXPOSE 80

# Run Nginx in the foreground
ENTRYPOINT ["nginx", "-g", "daemon off;"]

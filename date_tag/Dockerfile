# Use a lightweight Nginx image
FROM nginx:stable-alpine

# Copy the static files to the Nginx html directory
COPY index.html /usr/share/nginx/html/
COPY index.css /usr/share/nginx/html/
COPY index.js /usr/share/nginx/html/

# Expose port 80
EXPOSE 80

# Nginx starts automatically

FROM leantime/leantime:latest

# Switch to root to modify nginx config
USER root

# Fix nginx to listen on port 80 instead of 8080
RUN sed -i 's/listen 8080;/listen 80;/' /etc/nginx/nginx.conf

# Verify the change
RUN grep "listen 80;" /etc/nginx/nginx.conf

# Switch back to www-data
USER www-data

#!/bin/bash
# Go from zero to basic web host on an aws ubuntu instance
#
# Variables
DOMAIN="yourdomain.com"
EMAIL="youremail@example.com"
FLASK_APP_PORT=5000
NGINX_CONF="/etc/nginx/sites-available/$DOMAIN"
NGINX_CONF_LINK="/etc/nginx/sites-enabled/$DOMAIN"

# Function to check the status of the last executed command
check_status() {
    if [ $? -ne 0 ]; then
        echo "Error: $1"
        exit 1
    fi
}

# Update package list
echo "Updating package list..."
sudo apt update
check_status "Failed to update package list."

# Install Nginx
echo "Installing Nginx..."
sudo apt install -y nginx
check_status "Failed to install Nginx."

# Install Certbot and Nginx plugin
echo "Installing Certbot and Nginx plugin..."
sudo apt install -y certbot python3-certbot-nginx
check_status "Failed to install Certbot and Nginx plugin."

# Create Nginx configuration for the domain
echo "Creating Nginx configuration for $DOMAIN..."
sudo tee $NGINX_CONF > /dev/null <<EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    location / {
        proxy_pass http://127.0.0.1:$FLASK_APP_PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
check_status "Failed to create Nginx configuration."

# Enable the Nginx configuration
echo "Enabling Nginx configuration..."
sudo ln -s $NGINX_CONF $NGINX_CONF_LINK
check_status "Failed to enable Nginx configuration."

# Test Nginx configuration
echo "Testing Nginx configuration..."
sudo nginx -t
check_status "Nginx configuration test failed."

# Reload Nginx
echo "Reloading Nginx..."
sudo systemctl reload nginx
check_status "Failed to reload Nginx."

# Obtain SSL certificate
echo "Obtaining SSL certificate for $DOMAIN..."
sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN --non-interactive --agree-tos --email $EMAIL
check_status "Failed to obtain SSL certificate."

# Set up automatic certificate renewal
echo "Setting up automatic certificate renewal..."
sudo systemctl enable certbot.timer
check_status "Failed to enable Certbot timer."

echo "Setup completed successfully. Your Flask application is now accessible via HTTPS at https://$DOMAIN."


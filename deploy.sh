#!/bin/bash

# ArtAI Deployment Script for Ubuntu VPS
# This script sets up the ArtAI application for production deployment

echo "🎨 ArtAI Production Deployment Script"
echo "====================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run this script as root (use sudo)"
    exit 1
fi

# Update system packages
echo "📦 Updating system packages..."
apt update && apt upgrade -y

# Install required system packages
echo "🔧 Installing required system packages..."
apt install -y python3 python3-pip python3-venv nginx supervisor

# Create application directory
echo "📁 Setting up application directory..."
mkdir -p /var/www/artai
cd /var/www/artai

# Copy application files (assuming they're in the current directory)
echo "📋 Copying application files..."
cp -r * /var/www/artai/

# Set proper permissions
echo "🔐 Setting proper permissions..."
chown -R www-data:www-data /var/www/artai
chmod -R 755 /var/www/artai

# Create virtual environment
echo "🐍 Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "📚 Installing Python dependencies..."
pip install -r requirements.txt

# Initialize database
echo "🗄️ Initializing database..."
python3 start.py

# Create Gunicorn configuration
echo "⚙️ Creating Gunicorn configuration..."
cat > /etc/supervisor/conf.d/artai.conf << EOF
[program:artai]
directory=/var/www/artai
command=/var/www/artai/venv/bin/gunicorn --workers 3 --bind unix:artai.sock -m 007 app:app
autostart=true
autorestart=true
stderr_logfile=/var/log/artai/artai.err.log
stdout_logfile=/var/log/artai/artai.out.log
user=www-data
group=www-data
environment=PATH="/var/www/artai/venv/bin"
EOF

# Create log directory
mkdir -p /var/log/artai
chown -R www-data:www-data /var/log/artai

# Create Nginx configuration
echo "🌐 Creating Nginx configuration..."
cat > /etc/nginx/sites-available/artai << EOF
server {
    listen 80;
    server_name _;

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/artai/artai.sock;
    }

    location /static {
        alias /var/www/artai/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /uploads {
        alias /var/www/artai/uploads;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# Enable Nginx site
echo "🔗 Enabling Nginx site..."
ln -sf /etc/nginx/sites-available/artai /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
echo "🧪 Testing Nginx configuration..."
nginx -t

if [ $? -eq 0 ]; then
    echo "✅ Nginx configuration is valid"
else
    echo "❌ Nginx configuration has errors"
    exit 1
fi

# Start services
echo "🚀 Starting services..."
systemctl restart supervisor
systemctl restart nginx
systemctl enable supervisor
systemctl enable nginx

# Create firewall rules (if ufw is available)
if command -v ufw &> /dev/null; then
    echo "🔥 Configuring firewall..."
    ufw allow 'Nginx Full'
    ufw allow ssh
    ufw --force enable
fi

# Create systemd service for auto-start
echo "⚡ Creating systemd service..."
cat > /etc/systemd/system/artai.service << EOF
[Unit]
Description=ArtAI Gunicorn Application
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/artai
Environment="PATH=/var/www/artai/venv/bin"
ExecStart=/var/www/artai/venv/bin/gunicorn --workers 3 --bind unix:artai.sock -m 007 app:app
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Enable and start the service
systemctl daemon-reload
systemctl enable artai
systemctl start artai

# Create environment file
echo "🔧 Creating environment configuration..."
cat > /var/www/artai/.env << EOF
FLASK_ENV=production
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
DATABASE_URL=sqlite:////var/www/artai/artai.db
UPLOAD_FOLDER=/var/www/artai/uploads
MAX_CONTENT_LENGTH=16777216
EOF

chown www-data:www-data /var/www/artai/.env
chmod 600 /var/www/artai/.env

# Create uploads directory
mkdir -p /var/www/artai/uploads
chown -R www-data:www-data /var/www/artai/uploads
chmod -R 755 /var/www/artai/uploads

echo ""
echo "🎉 ArtAI has been successfully deployed!"
echo "========================================"
echo "🌐 Application URL: http://your-server-ip"
echo "👤 Admin Login: admin / admin123"
echo "📁 Application Directory: /var/www/artai"
echo "📋 Logs: /var/log/artai/"
echo ""
echo "🔧 Useful commands:"
echo "  - Check status: systemctl status artai"
echo "  - View logs: tail -f /var/log/artai/artai.out.log"
echo "  - Restart app: systemctl restart artai"
echo "  - Update app: cd /var/www/artai && git pull && systemctl restart artai"
echo ""
echo "⚠️  Don't forget to:"
echo "  1. Change the admin password after first login"
echo "  2. Configure your domain name in Nginx"
echo "  3. Set up SSL certificates with Let's Encrypt"
echo "  4. Configure regular backups"
echo ""
# CodeSync Deployment Guide - Oracle Cloud Always Free Tier

## Why Oracle Cloud Always Free?

- **Always Free**: Not just 12-month trial - permanently free tier
- **Better Performance**: Full VM control vs Render's limitations
- **No SSL Issues**: Full control over TLS/SSL configuration
- **More Resources**: Up to 24GB RAM and 200GB storage across 4 VMs

## Step 1: Oracle Cloud Setup

1. **Create Oracle Cloud Account**: https://cloud.oracle.com/free
2. **Create Compute Instance**:
   - Shape: VM.Standard.E2.1.Micro (Always Free)
   - Image: Ubuntu 20.04 or 22.04
   - Network: Create VCN with public subnet
   - Security: Add ingress rules for ports 80, 443, 3000, 8000

## Step 2: Server Setup

### Initial Server Configuration
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Node.js 18
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install Python 3.11 and pip
sudo apt install python3.11 python3.11-venv python3-pip -y

# Install yarn
npm install -g yarn

# Install nginx for reverse proxy
sudo apt install nginx -y

# Install certbot for SSL certificates
sudo apt install certbot python3-certbot-nginx -y
```

### Application Deployment
```bash
# Clone repository
git clone <your-repo-url> /opt/codesync
cd /opt/codesync

# Backend setup
cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Frontend setup  
cd ../frontend
yarn install
yarn build
```

## Step 3: Environment Configuration

### Backend Environment
```bash
# Create /opt/codesync/backend/.env
MONGO_URL="mongodb+srv://abhibhavr:aryanraj@codesync-cluster.n3jdeuf.mongodb.net/?retryWrites=true&w=majority&appName=codesync-cluster"
DB_NAME="codesync"
```

### Frontend Environment
```bash
# Create /opt/codesync/frontend/.env
REACT_APP_BACKEND_URL=https://your-domain.com
```

## Step 4: Process Management with PM2

```bash
# Install PM2
sudo npm install -g pm2

# Create PM2 ecosystem file
cat > /opt/codesync/ecosystem.config.js << 'EOF'
module.exports = {
  apps: [
    {
      name: 'codesync-backend',
      cwd: '/opt/codesync/backend',
      script: 'venv/bin/python',
      args: '-m uvicorn server:app --host 0.0.0.0 --port 8000',
      env: {
        MONGO_URL: process.env.MONGO_URL,
        DB_NAME: process.env.DB_NAME
      },
      instances: 1,
      exec_mode: 'fork',
      watch: false,
      max_memory_restart: '500M'
    },
    {
      name: 'codesync-frontend',
      cwd: '/opt/codesync/frontend',
      script: 'serve',
      args: '-s build -l 3000',
      instances: 1,
      exec_mode: 'fork',
      watch: false
    }
  ]
}
EOF

# Install serve for frontend
npm install -g serve

# Start applications
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

## Step 5: Nginx Reverse Proxy

```bash
# Create nginx configuration
sudo tee /etc/nginx/sites-available/codesync << 'EOF'
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    
    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
    
    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
    
    # SSE endpoint
    location /api/sse {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'keep-alive';
        proxy_set_header Host $host;
        proxy_set_header Cache-Control 'no-cache';
        proxy_set_header X-Accel-Buffering 'no';
        proxy_read_timeout 24h;
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/codesync /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

## Step 6: SSL Certificate (Optional)

```bash
# Get SSL certificate from Let's Encrypt
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

## Step 7: Firewall Configuration

```bash
# Configure UFW firewall
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable
```

## Step 8: Monitoring and Logs

```bash
# View application logs
pm2 logs

# View nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Monitor system resources
htop
pm2 monit
```

## Migration from Render

If you need to migrate from Render to Oracle Cloud:

1. **Export Data**: Export any data from your current deployment
2. **Update DNS**: Point your domain to Oracle Cloud instance IP
3. **Test Thoroughly**: Verify all functionality works
4. **Update Environment Variables**: Ensure all configs are correct

## Cost Comparison

- **Render**: $7-25/month for production apps
- **Oracle Cloud Always Free**: $0/month permanently
- **Performance**: Oracle Cloud provides better control and performance

## Support and Maintenance

- **Automatic Restart**: PM2 handles application crashes
- **System Updates**: Regular `apt update && apt upgrade`
- **SSL Renewal**: Certbot auto-renews SSL certificates
- **Monitoring**: PM2 provides built-in monitoring
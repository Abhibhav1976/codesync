# CodeSync Deployment Guide - Render

## Quick Deployment Steps

### 1. Backend Deployment (Render Web Service)

1. **Create New Web Service** in Render dashboard
   - Connect your GitHub repository
   - Select the repository root directory

2. **Configure Build & Start Commands**:
   ```bash
   # Build Command
   cd backend && pip install -r requirements.txt
   
   # Start Command  
   cd backend && python start.py
   ```

3. **Environment Variables**:
   ```
   MONGO_URL = mongodb+srv://abhibhavr:aryanraj@codesync-cluster.n3jdeuf.mongodb.net/?retryWrites=true&w=majority&appName=codesync-cluster
   DB_NAME = codesync
   ```

4. **Runtime Settings**:
   - Python Version: 3.11.0
   - Region: Choose closest to your users
   - Instance Type: Free tier initially

### 2. Frontend Deployment (Render Static Site)

1. **Create New Static Site** in Render dashboard
2. **Configure Build Settings**:
   ```bash
   # Build Command
   cd frontend && yarn install && yarn build
   
   # Publish Directory
   frontend/build
   ```

3. **Environment Variables**:
   ```
   REACT_APP_BACKEND_URL = https://your-backend-service-name.onrender.com
   ```

### 3. Important Notes

- **MongoDB Atlas**: Ensure your MongoDB Atlas cluster allows connections from `0.0.0.0/0` (all IPs)
- **CORS**: The backend is configured to allow all origins for development
- **SSL**: Fixed MongoDB Atlas SSL configuration using `tls=True` instead of deprecated `ssl=True`
- **Connection Pooling**: Optimized for serverless deployment with reduced pool sizes

### 4. Verification Steps

After deployment:

1. **Backend Health Check**:
   ```
   GET https://your-backend-service.onrender.com/health
   ```

2. **Test Room Creation**:
   ```bash
   curl -X POST https://your-backend-service.onrender.com/api/rooms \
     -H "Content-Type: application/json" \
     -d '{"name": "test-room", "language": "javascript"}'
   ```

3. **Frontend Access**:
   - Visit your static site URL
   - Try creating and joining a room
   - Test code execution and chat features

### 5. Troubleshooting

If you encounter SSL handshake errors:

1. Check MongoDB Atlas network access (should be `0.0.0.0/0`)
2. Verify connection string format in environment variables
3. Review Render deployment logs for specific error messages

### 6. Alternative: Oracle Cloud Free Tier

If Render continues to have issues, we can migrate to Oracle Cloud Always Free tier:

- 2 AMD-based Compute VMs with 1/8 OCPU and 1 GB memory each
- 200 GB Block Volume storage
- Always available (not just 12 months)
- Full control over the server environment

The deployment files are ready for Oracle Cloud migration if needed.
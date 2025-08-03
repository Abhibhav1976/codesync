# Real-Time Collaborative Code Editor

[![Live Demo](https://a7f2e870-c985-4fde-8c31-0b78dd933703.preview.emergentagent.com)
[![Backend](https://img.shields.io/badge/Backend-FastAPI-green)](https://fastapi.tiangolo.com/)
[![Frontend](https://img.shields.io/badge/Frontend-React-blue)](https://reactjs.org/)
[![Database](https://img.shields.io/badge/Database-MongoDB-green)](https://www.mongodb.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> A production-quality, browser-based collaborative code editor similar to VS Code, enabling real-time multi-user collaboration with syntax highlighting, file operations, and seamless synchronization.

![Real-Time Code Editor Screenshot](https://via.placeholder.com/800x400/1e293b/ffffff?text=Real-Time+Collaborative+Code+Editor)

---

## 🚀 Features

### 🎯 **Real-Time Collaboration**
- **Live Code Synchronization**: See changes from other users instantly as they type
- **Multi-User Presence**: Track who's in the room with live user indicators
- **Cursor Position Sharing**: See where other users are editing in real-time
- **Room-Based Sessions**: Create and join collaborative coding sessions with unique Room IDs

### 💻 **Professional Code Editor**
- **Monaco Editor Integration**: Full VS Code editor experience in the browser
- **Syntax Highlighting**: Support for JavaScript, Python, C++, TypeScript, HTML, CSS
- **Advanced Features**: Auto-indent, bracket matching, word wrap, line numbers
- **Language Switching**: Change programming languages with appropriate code templates

### 🏢 **Room Management**
- **Create Rooms**: Start new collaborative sessions with custom names
- **Join by ID**: Enter Room ID to join existing collaboration sessions
- **Persistent Storage**: Rooms and code saved to MongoDB database
- **Connection Monitoring**: Real-time connection status and user presence

### 💾 **File Operations**
- **Save to Database**: Persist code changes with automatic syncing
- **Download Files**: Export code with proper file extensions
- **Reset Templates**: Start fresh with language-specific code templates
- **Copy Room ID**: Easy sharing with clipboard integration and fallbacks

### 🎨 **Modern UI/UX**
- **Beautiful Dark Theme**: Professional interface with gradient backgrounds
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile
- **Real-time Feedback**: Live status updates and user notifications
- **Professional Components**: Built with shadcn/ui and Tailwind CSS

---

## 🏗️ Architecture

### **Tech Stack**
- **Frontend**: React 19, Monaco Editor, Tailwind CSS, shadcn/ui
- **Backend**: FastAPI, Python 3.11+
- **Database**: MongoDB with Motor (async driver)
- **Real-time**: Server-Sent Events (SSE) + HTTP APIs
- **Deployment**: Docker, Kubernetes-ready

### **System Design**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Client  │    │  FastAPI Server │    │   MongoDB DB    │
│                 │    │                 │    │                 │
│ Monaco Editor   │◄──►│ SSE Streams     │◄──►│ Room Storage    │
│ SSE Connection  │    │ REST APIs       │    │ Code Persistence│
│ HTTP Requests   │    │ User Sessions   │    │ User Management │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### **Real-Time Communication Flow**
1. **Client → Server**: HTTP POST requests for code/cursor updates
2. **Server → Clients**: SSE streams broadcast changes to room participants
3. **Database**: Persistent storage for rooms, code, and user sessions
4. **Auto-Reconnection**: Automatic SSE reconnection on connection loss

---

## 🚀 Quick Start

### **Prerequisites**
- Node.js 18+ and yarn
- Python 3.11+
- MongoDB (local or cloud)

### **1. Clone Repository**
```bash
git clone <repository-url>
cd real-time-code-editor
```

### **2. Backend Setup**
```bash
cd backend
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your MongoDB connection string

# Start backend server
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

### **3. Frontend Setup**
```bash
cd frontend
yarn install

# Configure environment  
cp .env.example .env
# Edit .env with your backend URL

# Start frontend development server
yarn start
```

### **4. Access Application**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8001/api
- API Documentation: http://localhost:8001/docs

---

## 📖 How to Use

### **Creating a Collaboration Session**
1. **Open the Application** in your browser
2. **Click "New Room"** button in the top-right corner
3. **Enter Room Name** and **select programming language**
4. **Click "Create Room"** - you'll automatically join the new session
5. **Share the Room ID** with collaborators (copy button available)

### **Joining an Existing Session**
1. **Click "Join Room"** button in the top-right corner
2. **Enter the Room ID** shared by the room creator
3. **Click "Join Room"** - you'll connect to the collaborative session
4. **Start coding together** - see real-time updates from all participants

### **Real-Time Collaboration Features**
- **Live Typing**: See code changes from other users in real-time
- **User Presence**: View list of connected users in the "Connected Users" panel
- **Connection Status**: Monitor your connection status (Connected/Disconnected)
- **Auto-Sync**: Code automatically syncs across all users in the room

### **File Operations**
- **Save**: Persist current code to database (Ctrl+S or Save button)
- **Reset**: Clear editor and load language template
- **Download**: Export code as file with proper extension
- **Language Switch**: Change language and get appropriate code template

---

## 🛠️ Development

### **Project Structure**
```
real-time-code-editor/
├── README.md                   # Project documentation
├── progress.md                 # Development progress log
├── .gitignore                  # Git ignore rules
├── backend/                    # FastAPI backend
│   ├── server.py              # Main FastAPI application
│   ├── requirements.txt       # Python dependencies
│   ├── .env.example          # Environment template
│   └── .env                  # Environment variables (local)
├── frontend/                  # React frontend
│   ├── package.json          # Node.js dependencies and scripts
│   ├── tailwind.config.js    # Tailwind CSS configuration
│   ├── postcss.config.js     # PostCSS configuration
│   ├── .env.example          # Environment template
│   ├── .env                  # Environment variables (local)
│   ├── public/               # Static assets
│   └── src/                  # React source code
│       ├── index.js          # Application entry point
│       ├── App.js            # Main React component
│       ├── App.css           # Component styles
│       └── components/ui/    # shadcn/ui components
└── scripts/                  # Utility scripts
```

### **API Endpoints**

#### **Room Management**
- `POST /api/rooms` - Create new room
- `GET /api/rooms/{room_id}` - Get room details
- `POST /api/rooms/join` - Join existing room
- `POST /api/rooms/{room_id}/save` - Save room code

#### **Real-Time Collaboration**
- `GET /api/sse/{user_id}` - SSE stream for real-time updates
- `POST /api/rooms/code` - Update room code
- `POST /api/rooms/cursor` - Update cursor position

#### **Health & Status**
- `GET /api/` - API health check
- `GET /api/status` - System status

### **Environment Variables**

#### **Backend (.env)**
```env
MONGO_URL=mongodb://localhost:27017
DB_NAME=code_editor_db
```

#### **Frontend (.env)**
```env
REACT_APP_BACKEND_URL=http://localhost:8001
```

### **Development Commands**

#### **Backend**
```bash
# Start development server
uvicorn server:app --host 0.0.0.0 --port 8001 --reload

# Run tests
python -m pytest

# Format code
black . && isort .
```

#### **Frontend**
```bash
# Start development server
yarn start

# Build for production
yarn build

# Run tests  
yarn test
```

---

## 🚀 Deployment

### **Docker Deployment**

#### **Backend Dockerfile**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8001
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001"]
```

#### **Frontend Dockerfile**
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package.json yarn.lock ./
RUN yarn install
COPY . .
RUN yarn build
EXPOSE 3000
CMD ["yarn", "start"]
```

### **Kubernetes Deployment**
The application is Kubernetes-ready with:
- `/api/*` routes directed to backend service
- SSE endpoints properly configured
- Environment variable injection
- Persistent volume claims for MongoDB

### **Production Considerations**
- **SSL/TLS**: Enable HTTPS for secure SSE connections
- **Rate Limiting**: Implement API rate limiting for production
- **Monitoring**: Add health checks and monitoring
- **Scaling**: Horizontal scaling with session affinity for SSE
- **Database**: Use MongoDB Atlas or managed database service

---

## 🧪 Testing

### **Backend Testing**
```bash
cd backend
python backend_test.py
```

**Test Coverage:**
- API endpoint functionality
- Room creation and management  
- Real-time collaboration features
- Error handling and edge cases
- SSE connection stability

### **Frontend Testing**
```bash
cd frontend
yarn test
```

**Test Areas:**
- Component rendering
- User interactions
- SSE connection handling
- Room joining and creation flows
- Monaco Editor integration

---

## 🔧 Technical Deep Dive

### **Why Server-Sent Events (SSE)?**
Initially designed with WebSocket architecture, the project evolved to use SSE for several advantages:

1. **Kubernetes Compatibility**: Better support for standard HTTP infrastructure
2. **Automatic Reconnection**: Built-in browser reconnection handling
3. **Simpler Implementation**: Less complex than bidirectional WebSocket management
4. **Firewall Friendly**: Works through standard HTTP proxies and firewalls

### **Real-Time Synchronization Strategy**
- **Debounced Updates**: 300ms debounce on code changes to optimize performance
- **Conflict Resolution**: Last-write-wins strategy with user attribution
- **Connection Management**: Automatic cleanup of disconnected users
- **State Synchronization**: Full state sync on room join

### **Performance Optimizations**
- **Monaco Editor**: Lazy loading and optimized configuration
- **SSE Streams**: Keep-alive pings every 30 seconds
- **Database Queries**: Indexed room lookups and user sessions
- **Frontend Rendering**: React.memo and useCallback optimizations

---

## 🤝 Contributing

### **Development Workflow**
1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Make changes and add tests
4. Commit changes: `git commit -m 'Add amazing feature'`
5. Push to branch: `git push origin feature/amazing-feature`
6. Open Pull Request

### **Code Standards**
- **Backend**: Black formatter, isort imports, type hints
- **Frontend**: ESLint, Prettier, React best practices
- **Commits**: Conventional commit messages
- **Testing**: Comprehensive test coverage for new features

### **Reporting Issues**
- Use GitHub Issues with clear reproduction steps
- Include browser/environment information
- Provide error logs and screenshots when applicable

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Monaco Editor** - Microsoft's excellent code editor
- **FastAPI** - Modern, fast web framework for Python
- **React** - Popular JavaScript library for user interfaces
- **shadcn/ui** - Beautiful and accessible component library
- **Tailwind CSS** - Utility-first CSS framework

---

## 📞 Support

- **Documentation**: This README and inline code comments
- **Issues**: GitHub Issues for bug reports and feature requests
- **Discussions**: GitHub Discussions for questions and community support

---

**🎉 Happy Collaborative Coding!** 

Built with ❤️ for developers who love to code together in real-time.
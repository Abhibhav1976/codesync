import React, { useState, useEffect, useRef } from 'react';
import { io } from 'socket.io-client';
import MonacoEditor from '@monaco-editor/react';
import { v4 as uuidv4 } from 'uuid';
import { Button } from './components/ui/button';
import { Input } from './components/ui/input';
import { Card, CardHeader, CardContent, CardTitle } from './components/ui/card';
import { Badge } from './components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from './components/ui/dialog';
import { Separator } from './components/ui/separator';
import { Save, Download, RotateCcw, Users, Copy, PlusCircle } from 'lucide-react';
import axios from 'axios';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [socket, setSocket] = useState(null);
  const [roomId, setRoomId] = useState('');
  const [userId, setUserId] = useState('');
  const [roomName, setRoomName] = useState('');
  const [code, setCode] = useState('// Welcome to Real-Time Code Editor!\n// Create a new room or join an existing one to start collaborating.\n\nconsole.log("Hello, World!");');
  const [language, setLanguage] = useState('javascript');
  const [connectedUsers, setConnectedUsers] = useState([]);
  const [cursors, setCursors] = useState({});
  const [isConnected, setIsConnected] = useState(false);
  const [isInRoom, setIsInRoom] = useState(false);
  const [newRoomName, setNewRoomName] = useState('');
  const [newRoomLanguage, setNewRoomLanguage] = useState('javascript');
  const [joinRoomId, setJoinRoomId] = useState('');
  const [statusMessage, setStatusMessage] = useState('');
  const [isCreateRoomOpen, setIsCreateRoomOpen] = useState(false);
  const [isJoinRoomOpen, setIsJoinRoomOpen] = useState(false);
  
  const editorRef = useRef(null);
  const monacoRef = useRef(null);

  const languages = [
    { value: 'javascript', label: 'JavaScript' },
    { value: 'python', label: 'Python' },
    { value: 'cpp', label: 'C++' },
    { value: 'typescript', label: 'TypeScript' },
    { value: 'html', label: 'HTML' },
    { value: 'css', label: 'CSS' }
  ];

  useEffect(() => {
    // Initialize socket connection
    const newSocket = io(BACKEND_URL, {
      transports: ['websocket', 'polling']
    });

    newSocket.on('connect', () => {
      console.log('Connected to server');
      setIsConnected(true);
      setStatusMessage('Connected to server');
    });

    newSocket.on('disconnect', () => {
      console.log('Disconnected from server');
      setIsConnected(false);
      setIsInRoom(false);
      setStatusMessage('Disconnected from server');
    });

    newSocket.on('room_joined', (data) => {
      setRoomId(data.room_id);
      setRoomName(data.room_name);
      setCode(data.code);
      setLanguage(data.language);
      setUserId(data.user_id);
      setConnectedUsers(data.users);
      setIsInRoom(true);
      setStatusMessage(`Joined room: ${data.room_name}`);
      setIsCreateRoomOpen(false);
      setIsJoinRoomOpen(false);
    });

    newSocket.on('user_joined', (data) => {
      setConnectedUsers(data.users);
      setStatusMessage(`${data.user_id} joined the room`);
    });

    newSocket.on('user_left', (data) => {
      setConnectedUsers(data.users);
      setStatusMessage(`${data.user_id} left the room`);
    });

    newSocket.on('code_updated', (data) => {
      if (data.user_id !== userId) {
        setCode(data.code);
      }
    });

    newSocket.on('cursor_updated', (data) => {
      setCursors(prev => ({
        ...prev,
        [data.user_id]: data.position
      }));
    });

    newSocket.on('file_saved', (data) => {
      setStatusMessage(data.message);
    });

    newSocket.on('error', (data) => {
      setStatusMessage(`Error: ${data.message}`);
    });

    setSocket(newSocket);

    return () => {
      newSocket.close();
    };
  }, []);

  const handleEditorDidMount = (editor, monaco) => {
    editorRef.current = editor;
    monacoRef.current = monaco;

    // Handle cursor position changes
    editor.onDidChangeCursorPosition((e) => {
      if (socket && isInRoom) {
        const position = {
          line: e.position.lineNumber,
          column: e.position.column
        };
        socket.emit('cursor_change', { position });
      }
    });
  };

  const handleCodeChange = (value) => {
    setCode(value);
    if (socket && isInRoom) {
      socket.emit('code_change', { code: value });
    }
  };

  const createRoom = async () => {
    if (!newRoomName.trim()) {
      setStatusMessage('Please enter a room name');
      return;
    }

    try {
      const response = await axios.post(`${API}/rooms`, {
        name: newRoomName,
        language: newRoomLanguage
      });

      const roomData = response.data;
      if (socket) {
        socket.emit('join_room', { room_id: roomData.id });
      }
    } catch (error) {
      console.error('Error creating room:', error);
      setStatusMessage('Failed to create room');
    }
  };

  const joinRoom = () => {
    if (!joinRoomId.trim()) {
      setStatusMessage('Please enter a room ID');
      return;
    }

    if (socket) {
      socket.emit('join_room', { room_id: joinRoomId });
    }
  };

  const saveFile = () => {
    if (socket && isInRoom) {
      socket.emit('save_file', {});
    }
  };

  const resetCode = () => {
    const defaultCode = getDefaultCodeForLanguage(language);
    setCode(defaultCode);
    if (socket && isInRoom) {
      socket.emit('code_change', { code: defaultCode });
    }
  };

  const downloadFile = () => {
    const element = document.createElement('a');
    const file = new Blob([code], { type: 'text/plain' });
    element.href = URL.createObjectURL(file);
    element.download = `code.${getFileExtension(language)}`;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  const copyRoomId = () => {
    navigator.clipboard.writeText(roomId);
    setStatusMessage('Room ID copied to clipboard');
  };

  const getDefaultCodeForLanguage = (lang) => {
    switch (lang) {
      case 'javascript':
        return '// JavaScript Code\nconsole.log("Hello, World!");';
      case 'python':
        return '# Python Code\nprint("Hello, World!")';
      case 'cpp':
        return '#include <iostream>\nusing namespace std;\n\nint main() {\n    cout << "Hello, World!" << endl;\n    return 0;\n}';
      case 'typescript':
        return '// TypeScript Code\nconst message: string = "Hello, World!";\nconsole.log(message);';
      case 'html':
        return '<!DOCTYPE html>\n<html>\n<head>\n    <title>Hello World</title>\n</head>\n<body>\n    <h1>Hello, World!</h1>\n</body>\n</html>';
      case 'css':
        return '/* CSS Code */\nbody {\n    font-family: Arial, sans-serif;\n    background-color: #f0f0f0;\n}\n\nh1 {\n    color: #333;\n    text-align: center;\n}';
      default:
        return '// Welcome to Real-Time Code Editor!';
    }
  };

  const getFileExtension = (lang) => {
    switch (lang) {
      case 'javascript': return 'js';
      case 'python': return 'py';
      case 'cpp': return 'cpp';
      case 'typescript': return 'ts';
      case 'html': return 'html';
      case 'css': return 'css';
      default: return 'txt';
    }
  };

  const handleLanguageChange = (newLanguage) => {
    setLanguage(newLanguage);
    const defaultCode = getDefaultCodeForLanguage(newLanguage);
    setCode(defaultCode);
    if (socket && isInRoom) {
      socket.emit('code_change', { code: defaultCode });
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      <div className="container mx-auto p-6">
        {/* Header */}
        <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center mb-6 gap-4">
          <div>
            <h1 className="text-4xl font-bold text-white mb-2">Real-Time Code Editor</h1>
            <p className="text-slate-300">Collaborate on code in real-time with multiple users</p>
          </div>
          
          <div className="flex flex-col sm:flex-row gap-3">
            <Dialog open={isCreateRoomOpen} onOpenChange={setIsCreateRoomOpen}>
              <DialogTrigger asChild>
                <Button className="bg-blue-600 hover:bg-blue-700 text-white">
                  <PlusCircle className="w-4 h-4 mr-2" />
                  New Room
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Create New Room</DialogTitle>
                </DialogHeader>
                <div className="space-y-4">
                  <Input
                    placeholder="Room name"
                    value={newRoomName}
                    onChange={(e) => setNewRoomName(e.target.value)}
                  />
                  <Select value={newRoomLanguage} onValueChange={setNewRoomLanguage}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select language" />
                    </SelectTrigger>
                    <SelectContent>
                      {languages.map((lang) => (
                        <SelectItem key={lang.value} value={lang.value}>
                          {lang.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Button onClick={createRoom} className="w-full">
                    Create Room
                  </Button>
                </div>
              </DialogContent>
            </Dialog>

            <Dialog open={isJoinRoomOpen} onOpenChange={setIsJoinRoomOpen}>
              <DialogTrigger asChild>
                <Button variant="outline" className="border-slate-600 text-slate-200 hover:bg-slate-800">
                  <Users className="w-4 h-4 mr-2" />
                  Join Room
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Join Room</DialogTitle>
                </DialogHeader>
                <div className="space-y-4">
                  <Input
                    placeholder="Enter room ID"
                    value={joinRoomId}
                    onChange={(e) => setJoinRoomId(e.target.value)}
                  />
                  <Button onClick={joinRoom} className="w-full">
                    Join Room
                  </Button>
                </div>
              </DialogContent>
            </Dialog>
          </div>
        </div>

        {/* Status and Room Info */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-6">
          <Card className="bg-slate-800 border-slate-700">
            <CardHeader className="pb-3">
              <CardTitle className="text-white text-sm">Connection Status</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
                <span className="text-slate-300 text-sm">
                  {isConnected ? 'Connected' : 'Disconnected'}
                </span>
              </div>
            </CardContent>
          </Card>

          {isInRoom && (
            <>
              <Card className="bg-slate-800 border-slate-700">
                <CardHeader className="pb-3">
                  <CardTitle className="text-white text-sm">Room Info</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-slate-300 text-sm">{roomName}</span>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={copyRoomId}
                        className="text-blue-400 hover:text-blue-300 p-1"
                      >
                        <Copy className="w-3 h-3" />
                      </Button>
                    </div>
                    <Badge variant="secondary" className="text-xs">
                      {userId}
                    </Badge>
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-slate-800 border-slate-700">
                <CardHeader className="pb-3">
                  <CardTitle className="text-white text-sm">Connected Users ({connectedUsers.length})</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-wrap gap-1">
                    {connectedUsers.map((user, index) => (
                      <Badge
                        key={user.user_id}
                        variant={user.user_id === userId ? "default" : "secondary"}
                        className="text-xs"
                      >
                        {user.user_id}
                      </Badge>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </>
          )}
        </div>

        {/* Editor Section */}
        <Card className="bg-slate-800 border-slate-700">
          <CardHeader>
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
              <div className="flex items-center gap-4">
                <Select value={language} onValueChange={handleLanguageChange}>
                  <SelectTrigger className="w-40 bg-slate-700 border-slate-600 text-white">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {languages.map((lang) => (
                      <SelectItem key={lang.value} value={lang.value}>
                        {lang.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="flex gap-2">
                <Button
                  onClick={saveFile}
                  disabled={!isInRoom}
                  className="bg-green-600 hover:bg-green-700 text-white"
                >
                  <Save className="w-4 h-4 mr-2" />
                  Save
                </Button>
                <Button
                  onClick={resetCode}
                  variant="outline"
                  className="border-slate-600 text-slate-200 hover:bg-slate-700"
                >
                  <RotateCcw className="w-4 h-4 mr-2" />
                  Reset
                </Button>
                <Button
                  onClick={downloadFile}
                  variant="outline"
                  className="border-slate-600 text-slate-200 hover:bg-slate-700"
                >
                  <Download className="w-4 h-4 mr-2" />
                  Download
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            <div className="h-96 lg:h-[600px] border border-slate-600 rounded-lg overflow-hidden">
              <MonacoEditor
                height="100%"
                language={language}
                value={code}
                onChange={handleCodeChange}
                onMount={handleEditorDidMount}
                theme="vs-dark"
                options={{
                  fontSize: 14,
                  minimap: { enabled: false },
                  scrollBeyondLastLine: false,
                  wordWrap: 'on',
                  automaticLayout: true,
                  tabSize: 2,
                  insertSpaces: true,
                  renderWhitespace: 'selection',
                  lineNumbers: 'on',
                  folding: true,
                  bracketMatching: 'always',
                  autoIndent: 'advanced'
                }}
              />
            </div>
          </CardContent>
        </Card>

        {/* Status Message */}
        {statusMessage && (
          <div className="mt-4">
            <Card className="bg-slate-800 border-slate-700">
              <CardContent className="py-3">
                <p className="text-slate-300 text-sm">{statusMessage}</p>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
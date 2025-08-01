import React, { useState, useEffect, useRef } from 'react';
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
  const [eventSource, setEventSource] = useState(null);
  const [roomId, setRoomId] = useState('');
  const [userId, setUserId] = useState(() => `user_${Math.random().toString(36).substr(2, 8)}`);
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
  const [statusMessage, setStatusMessage] = useState('Ready to connect');
  const [isCreateRoomOpen, setIsCreateRoomOpen] = useState(false);
  const [isJoinRoomOpen, setIsJoinRoomOpen] = useState(false);
  
  const editorRef = useRef(null);
  const monacoRef = useRef(null);
  const codeUpdateTimeoutRef = useRef(null);

  const languages = [
    { value: 'javascript', label: 'JavaScript' },
    { value: 'python', label: 'Python' },
    { value: 'cpp', label: 'C++' },
    { value: 'typescript', label: 'TypeScript' },
    { value: 'html', label: 'HTML' },
    { value: 'css', label: 'CSS' }
  ];

  useEffect(() => {
    // Initialize SSE connection when user joins a room
    if (isInRoom && roomId) {
      setupSSEConnection();
    }

    return () => {
      if (eventSource) {
        eventSource.close();
      }
    };
  }, [isInRoom, roomId, userId]);

  const setupSSEConnection = () => {
    if (eventSource) {
      eventSource.close();
    }

    console.log(`Setting up SSE connection for user: ${userId}`);
    const newEventSource = new EventSource(`${API}/sse/${userId}`);
    
    newEventSource.onopen = (event) => {
      console.log('SSE connection opened:', event);
      setIsConnected(true);
      setStatusMessage('Connected to real-time server');
    };

    newEventSource.onmessage = (event) => {
      try {
        console.log('SSE message received:', event.data);
        const data = JSON.parse(event.data);
        handleSSEMessage(data);
      } catch (error) {
        console.error('Error parsing SSE message:', error);
      }
    };

    newEventSource.onerror = (error) => {
      console.error('SSE connection error:', error);
      console.log('SSE readyState:', newEventSource.readyState);
      setIsConnected(false);
      setStatusMessage('Connection error - attempting to reconnect...');
      
      // Attempt to reconnect after a delay if still in room
      setTimeout(() => {
        if (isInRoom && newEventSource.readyState === EventSource.CLOSED) {
          console.log('Attempting SSE reconnection...');
          setupSSEConnection();
        }
      }, 5000);
    };

    setEventSource(newEventSource);
  };

  const handleSSEMessage = (message) => {
    const { type, data } = message;
    console.log('Handling SSE message:', type, data);

    switch (type) {
      case 'ping':
        // Keep-alive ping, no action needed
        console.log('Received SSE ping');
        break;
      
      case 'user_joined':
        setConnectedUsers(data.users);
        setStatusMessage(`${data.user_id} joined the room`);
        break;
      
      case 'user_left':
        setConnectedUsers(data.users);
        setStatusMessage(`${data.user_id} left the room`);
        break;
      
      case 'code_updated':
        console.log('Code updated by:', data.user_id);
        if (data.user_id !== userId) {
          setCode(data.code);
          setStatusMessage(`Code updated by ${data.user_id}`);
        }
        break;
      
      case 'cursor_updated':
        console.log('Cursor updated by:', data.user_id);
        setCursors(prev => ({
          ...prev,
          [data.user_id]: data.position
        }));
        break;
      
      default:
        console.log('Unknown SSE message type:', type, data);
    }
  };

  const handleEditorDidMount = (editor, monaco) => {
    editorRef.current = editor;
    monacoRef.current = monaco;

    // Handle cursor position changes
    editor.onDidChangeCursorPosition((e) => {
      if (isInRoom) {
        const position = {
          line: e.position.lineNumber,
          column: e.position.column
        };
        updateCursor(position);
      }
    });
  };

  const handleCodeChange = (value) => {
    setCode(value);
    
    if (isInRoom) {
      // Debounce code updates to avoid too many requests
      if (codeUpdateTimeoutRef.current) {
        clearTimeout(codeUpdateTimeoutRef.current);
      }
      
      codeUpdateTimeoutRef.current = setTimeout(() => {
        updateCode(value);
      }, 300); // 300ms debounce
    }
  };

  const updateCode = async (newCode) => {
    try {
      await axios.post(`${API}/rooms/code`, {
        room_id: roomId,
        code: newCode,
        user_id: userId
      });
    } catch (error) {
      console.error('Error updating code:', error);
      setStatusMessage('Failed to sync code changes');
    }
  };

  const updateCursor = async (position) => {
    try {
      await axios.post(`${API}/rooms/cursor`, {
        room_id: roomId,
        user_id: userId,
        position: position
      });
    } catch (error) {
      console.error('Error updating cursor:', error);
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
      await joinRoom(roomData.id);
    } catch (error) {
      console.error('Error creating room:', error);
      setStatusMessage('Failed to create room');
    }
  };

  const joinRoom = async (targetRoomId = null) => {
    const roomIdToJoin = targetRoomId || joinRoomId;
    
    if (!roomIdToJoin.trim()) {
      setStatusMessage('Please enter a room ID');
      return;
    }

    setStatusMessage('Joining room...');

    try {
      const response = await axios.post(`${API}/rooms/join`, {
        room_id: roomIdToJoin,
        user_id: userId
      });

      const data = response.data;
      
      if (data.error) {
        setStatusMessage(`Error: ${data.error}`);
        return;
      }

      // Successfully joined room - update all state
      setRoomId(data.room_id);
      setRoomName(data.room_name);
      setCode(data.code);
      setLanguage(data.language);
      setConnectedUsers(data.users);
      setIsInRoom(true);
      setStatusMessage(`Successfully joined room: ${data.room_name}`);
      setIsCreateRoomOpen(false);
      setIsJoinRoomOpen(false);
      setJoinRoomId('');
      setNewRoomName('');

      // SSE connection will be established by useEffect when isInRoom becomes true
      console.log('Room joined successfully:', data);
    } catch (error) {
      console.error('Error joining room:', error);
      if (error.response && error.response.data) {
        setStatusMessage(`Failed to join room: ${error.response.data.message || 'Unknown error'}`);
      } else {
        setStatusMessage('Failed to join room - please check your connection');
      }
    }
  };

  const saveFile = async () => {
    if (!isInRoom) return;

    try {
      await axios.post(`${API}/rooms/${roomId}/save`);
      setStatusMessage('File saved successfully');
    } catch (error) {
      console.error('Error saving file:', error);
      setStatusMessage('Failed to save file');
    }
  };

  const resetCode = async () => {
    const defaultCode = getDefaultCodeForLanguage(language);
    setCode(defaultCode);
    if (isInRoom) {
      await updateCode(defaultCode);
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

  const copyRoomId = async () => {
    try {
      await navigator.clipboard.writeText(roomId);
      setStatusMessage('Room ID copied to clipboard');
    } catch (error) {
      console.error('Clipboard write failed:', error);
      // Fallback method for browsers that don't support clipboard API
      const textArea = document.createElement('textarea');
      textArea.value = roomId;
      textArea.style.position = 'fixed';
      textArea.style.left = '-999999px';
      textArea.style.top = '-999999px';
      document.body.appendChild(textArea);
      textArea.focus();
      textArea.select();
      try {
        document.execCommand('copy');
        setStatusMessage('Room ID copied to clipboard');
      } catch (err) {
        console.error('Fallback copy failed:', err);
        setStatusMessage(`Room ID: ${roomId} (click to select)`);
        // Show the room ID in a selectable format
        const roomIdDisplay = document.createElement('div');
        roomIdDisplay.style.position = 'fixed';
        roomIdDisplay.style.top = '50%';
        roomIdDisplay.style.left = '50%';
        roomIdDisplay.style.transform = 'translate(-50%, -50%)';
        roomIdDisplay.style.background = 'white';
        roomIdDisplay.style.padding = '20px';
        roomIdDisplay.style.border = '2px solid #000';
        roomIdDisplay.style.zIndex = '10000';
        roomIdDisplay.style.color = 'black';
        roomIdDisplay.innerHTML = `<p>Copy this Room ID:</p><strong style="user-select: all;">${roomId}</strong><br><button onclick="this.parentElement.remove()">Close</button>`;
        document.body.appendChild(roomIdDisplay);
      }
      document.body.removeChild(textArea);
    }
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

  const handleLanguageChange = async (newLanguage) => {
    setLanguage(newLanguage);
    const defaultCode = getDefaultCodeForLanguage(newLanguage);
    setCode(defaultCode);
    if (isInRoom) {
      await updateCode(defaultCode);
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
                  <Button onClick={() => joinRoom()} className="w-full">
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
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
import { Save, Download, RotateCcw, Users, Copy, PlusCircle, Play, X, Send, MessageCircle, ChevronRight, ChevronLeft, Code, FileText, Plus, Trash2 } from 'lucide-react';
import axios from 'axios';
import { ThemeProvider, useTheme } from './contexts/ThemeContext';
import ThemeSelector from './components/ThemeSelector';
import UserAvatar from './components/UserAvatar';
import EmojiReaction from './components/EmojiReaction';
import RoomDeletion from './components/RoomDeletion';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function AppContent() {
  const { theme } = useTheme();
  const [eventSource, setEventSource] = useState(null);
  const [roomId, setRoomId] = useState('');
  const [userId, setUserId] = useState(() => `user_${Math.random().toString(36).substr(2, 8)}`);
  const [userName, setUserName] = useState(() => localStorage.getItem('userName') || '');
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
  
  // User naming states
  const [isUserNamePromptOpen, setIsUserNamePromptOpen] = useState(false);
  const [tempUserName, setTempUserName] = useState('');
  const [userNameError, setUserNameError] = useState('');
  const [pendingAction, setPendingAction] = useState(null); // 'create' or 'join'
  
  // Run code states
  const [isCodeRunning, setIsCodeRunning] = useState(false);
  const [codeOutput, setCodeOutput] = useState({ stdout: '', stderr: '', exit_code: 0 });
  const [showOutput, setShowOutput] = useState(false);
  
  // Chat states
  const [chatMessages, setChatMessages] = useState([]);
  const [newChatMessage, setNewChatMessage] = useState('');
  const [isSendingMessage, setIsSendingMessage] = useState(false);
  const [showChat, setShowChat] = useState(true);
  const [messageReactions, setMessageReactions] = useState({}); // messageId -> array of reactions
  
  // File tabs state
  const [openFiles, setOpenFiles] = useState([
    { id: 'main', name: 'main.js', language: 'javascript', content: code, isActive: true }
  ]);
  const [activeFileId, setActiveFileId] = useState('main');
  
  // Room deletion state
  const [isRoomDeletionOpen, setIsRoomDeletionOpen] = useState(false);
  
  const editorRef = useRef(null);
  const monacoRef = useRef(null);
  const codeUpdateTimeoutRef = useRef(null);
  const chatEndRef = useRef(null);

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

  // Auto-scroll chat to bottom when new messages arrive
  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [chatMessages]);

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
        setStatusMessage(`${data.user_name || data.user_id} joined the room`);
        break;
      
      case 'user_left':
        setConnectedUsers(data.users);
        setStatusMessage(`${data.user_name || data.user_id} left the room`);
        break;
      
      case 'code_updated':
        console.log('Code updated by:', data.user_id);
        if (data.user_id !== userId) {
          setCode(data.code);
          // Update the active file content
          setOpenFiles(files => files.map(file => 
            file.id === activeFileId ? { ...file, content: data.code } : file
          ));
          setStatusMessage(`Code updated by ${data.user_name || data.user_id}`);
        }
        break;
      
      case 'cursor_updated':
        console.log('Cursor updated by:', data.user_id);
        setCursors(prev => ({
          ...prev,
          [data.user_id]: data.position
        }));
        break;
      
      case 'chat_message':
        console.log('Chat message received:', data);
        setChatMessages(prev => [...prev, data]);
        setStatusMessage(`New message from ${data.user_name || data.user_id}`);
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

  // User name validation and management
  const validateUserName = (name) => {
    if (!name || name.trim().length === 0) {
      return "Please enter a display name";
    }
    if (name.length < 3) {
      return "Name must be at least 3 characters";
    }
    if (name.length > 15) {
      return "Name must be 15 characters or less";
    }
    if (!/^[a-zA-Z0-9_]+$/.test(name)) {
      return "Name can only contain letters, numbers, and underscores";
    }
    return "";
  };

  const promptForUserName = (action) => {
    if (!userName) {
      setPendingAction(action);
      setTempUserName('');
      setUserNameError('');
      setIsUserNamePromptOpen(true);
      return false;
    }
    return true;
  };

  const handleUserNameSubmit = () => {
    const error = validateUserName(tempUserName);
    if (error) {
      setUserNameError(error);
      return;
    }
    
    setUserName(tempUserName);
    localStorage.setItem('userName', tempUserName);
    setIsUserNamePromptOpen(false);
    
    // Execute the pending action
    if (pendingAction === 'create') {
      executeCreateRoom();
    } else if (pendingAction === 'join') {
      executeJoinRoom();
    }
    setPendingAction(null);
  };

  const handleCodeChange = (value) => {
    setCode(value);
    
    // Update the active file content
    setOpenFiles(files => files.map(file => 
      file.id === activeFileId ? { ...file, content: value } : file
    ));
    
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
        user_id: userId,
        user_name: userName
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
        user_name: userName,
        position: position
      });
    } catch (error) {
      console.error('Error updating cursor:', error);
    }
  };

  const sendChatMessage = async () => {
    if (!newChatMessage.trim() || isSendingMessage || !isInRoom) {
      return;
    }

    setIsSendingMessage(true);
    
    try {
      const response = await axios.post(`${API}/send-chat-message`, {
        room_id: roomId,
        user_id: userId,
        user_name: userName,
        message: newChatMessage.trim()
      });

      if (response.data.success) {
        setNewChatMessage(''); // Clear input after successful send
      } else if (response.data.error) {
        setStatusMessage(`Chat error: ${response.data.error}`);
      }
    } catch (error) {
      console.error('Error sending chat message:', error);
      setStatusMessage('Failed to send message');
    } finally {
      setIsSendingMessage(false);
    }
  };

  const handleChatKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendChatMessage();
    }
  };

  const handleMessageReaction = (messageId, reactionType) => {
    setMessageReactions(prev => {
      const messageReacts = prev[messageId] || [];
      const existingReaction = messageReacts.find(r => r.userId === userId && r.type === reactionType);
      
      if (existingReaction) {
        // Remove reaction
        return {
          ...prev,
          [messageId]: messageReacts.filter(r => !(r.userId === userId && r.type === reactionType))
        };
      } else {
        // Add reaction
        return {
          ...prev,
          [messageId]: [...messageReacts, { userId, type: reactionType, timestamp: Date.now() }]
        };
      }
    });
  };

  const createRoom = async () => {
    if (!promptForUserName('create')) {
      return;
    }
    executeCreateRoom();
  };

  const executeCreateRoom = async () => {
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
      await executeJoinRoom(roomData.id);
    } catch (error) {
      console.error('Error creating room:', error);
      setStatusMessage('Failed to create room');
    }
  };

  const joinRoom = async (targetRoomId = null) => {
    if (!promptForUserName('join')) {
      return;
    }
    executeJoinRoom(targetRoomId);
  };

  const executeJoinRoom = async (targetRoomId = null) => {
    const roomIdToJoin = targetRoomId || joinRoomId;
    
    if (!roomIdToJoin.trim()) {
      setStatusMessage('Please enter a room ID');
      return;
    }

    setStatusMessage('Joining room...');

    try {
      const response = await axios.post(`${API}/rooms/join`, {
        room_id: roomIdToJoin,
        user_id: userId,
        user_name: userName
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
      setChatMessages(data.chat_messages || []); // Load existing chat history
      setIsInRoom(true);
      setStatusMessage(`Successfully joined room: ${data.room_name}`);
      setIsCreateRoomOpen(false);
      setIsJoinRoomOpen(false);
      setJoinRoomId('');
      setNewRoomName('');

      // Update file tabs
      setOpenFiles([{
        id: 'main',
        name: `main.${getFileExtension(data.language)}`,
        language: data.language,
        content: data.code,
        isActive: true
      }]);

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
    
    // Update the active file content
    setOpenFiles(files => files.map(file => 
      file.id === activeFileId ? { ...file, content: defaultCode } : file
    ));
    
    if (isInRoom) {
      await updateCode(defaultCode);
    }
  };

  const downloadFile = () => {
    const activeFile = openFiles.find(f => f.id === activeFileId);
    const element = document.createElement('a');
    const file = new Blob([activeFile?.content || code], { type: 'text/plain' });
    element.href = URL.createObjectURL(file);
    element.download = activeFile?.name || `code.${getFileExtension(language)}`;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  const runCode = async () => {
    if (isCodeRunning) return;
    
    setIsCodeRunning(true);
    setStatusMessage('Running code...');
    setShowOutput(true);
    
    try {
      const response = await axios.post(`${API}/run-code`, {
        language: language,
        code: code,
        stdin: ""
      });
      
      const result = response.data;
      setCodeOutput({
        stdout: result.stdout || '',
        stderr: result.stderr || '',
        exit_code: result.exit_code || 0
      });
      
      if (result.exit_code === 0) {
        setStatusMessage('Code executed successfully');
      } else {
        setStatusMessage('Code execution completed with errors');
      }
    } catch (error) {
      console.error('Error running code:', error);
      setCodeOutput({
        stdout: '',
        stderr: error.response?.data?.message || 'Failed to execute code. Please try again.',
        exit_code: 1
      });
      setStatusMessage('Failed to run code');
    } finally {
      setIsCodeRunning(false);
    }
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
      }
      document.body.removeChild(textArea);
    }
  };

  const addNewFile = () => {
    const newFileId = `file_${Date.now()}`;
    const newFile = {
      id: newFileId,
      name: `untitled.${getFileExtension(language)}`,
      language: language,
      content: getDefaultCodeForLanguage(language),
      isActive: true
    };
    
    setOpenFiles(files => [
      ...files.map(f => ({ ...f, isActive: false })),
      newFile
    ]);
    setActiveFileId(newFileId);
    setCode(newFile.content);
  };

  const switchToFile = (fileId) => {
    const file = openFiles.find(f => f.id === fileId);
    if (file) {
      setOpenFiles(files => files.map(f => ({ ...f, isActive: f.id === fileId })));
      setActiveFileId(fileId);
      setCode(file.content);
      setLanguage(file.language);
    }
  };

  const closeFile = (fileId) => {
    if (openFiles.length <= 1) return; // Keep at least one file open
    
    const remainingFiles = openFiles.filter(f => f.id !== fileId);
    const wasActive = openFiles.find(f => f.id === fileId)?.isActive;
    
    if (wasActive) {
      const newActiveFile = remainingFiles[0];
      newActiveFile.isActive = true;
      setActiveFileId(newActiveFile.id);
      setCode(newActiveFile.content);
      setLanguage(newActiveFile.language);
    }
    
    setOpenFiles(remainingFiles);
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

  const handleRoomDeletion = () => {
    // Clear all room-related state
    setIsInRoom(false);
    setRoomId('');
    setRoomName('');
    setConnectedUsers([]);
    setChatMessages([]);
    setMessageReactions({});
    setCursors({});
    setCode('// Welcome to Real-Time Code Editor!\n// Create a new room or join an existing one to start collaborating.\n\nconsole.log("Hello, World!");');
    
    // Reset file tabs to default
    setOpenFiles([
      { id: 'main', name: 'main.js', language: 'javascript', content: '// Welcome to Real-Time Code Editor!\n// Create a new room or join an existing one to start collaborating.\n\nconsole.log("Hello, World!");', isActive: true }
    ]);
    setActiveFileId('main');
    
    // Close SSE connection
    if (eventSource) {
      eventSource.close();
      setEventSource(null);
    }
    
    setIsConnected(false);
    setStatusMessage('Room deleted successfully. Ready to create or join a new room.');
  };

  const handleLanguageChange = async (newLanguage) => {
    setLanguage(newLanguage);
    const defaultCode = getDefaultCodeForLanguage(newLanguage);
    setCode(defaultCode);
    
    // Update the active file
    setOpenFiles(files => files.map(file => 
      file.id === activeFileId 
        ? { ...file, language: newLanguage, content: defaultCode, name: `${file.name.split('.')[0]}.${getFileExtension(newLanguage)}` }
        : file
    ));
    
    if (isInRoom) {
      await updateCode(defaultCode);
    }
  };

  return (
    <div className={`min-h-screen bg-gradient-to-br ${theme.colors.background.primary}`}>
      <div className="container mx-auto p-6">
        {/* Header */}
        <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center mb-6 gap-4">
          <div>
            <h1 className={`text-4xl font-bold ${theme.colors.text.primary} mb-2`}>
              Real-Time Code Editor
            </h1>
            <p className={theme.colors.text.secondary}>
              Collaborate on code in real-time with multiple users
            </p>
          </div>
          
          <div className="flex flex-col sm:flex-row gap-3 items-center">
            <ThemeSelector />
            
            <Dialog open={isCreateRoomOpen} onOpenChange={setIsCreateRoomOpen}>
              <DialogTrigger asChild>
                <Button className={`${theme.colors.interactive.button.accent} ${theme.colors.text.primary} hover:scale-105 transform transition-all duration-200`}>
                  <PlusCircle className="w-4 h-4 mr-2" />
                  New Room
                </Button>
              </DialogTrigger>
              <DialogContent className={`${theme.colors.background.card} ${theme.colors.background.cardBorder} ${theme.colors.glow.card}`}>
                <DialogHeader>
                  <DialogTitle className={theme.colors.text.primary}>Create New Room</DialogTitle>
                </DialogHeader>
                <div className="space-y-4">
                  <Input
                    placeholder="Room name"
                    value={newRoomName}
                    onChange={(e) => setNewRoomName(e.target.value)}
                    className={theme.colors.interactive.input}
                  />
                  <Select value={newRoomLanguage} onValueChange={setNewRoomLanguage}>
                    <SelectTrigger className={theme.colors.interactive.select}>
                      <SelectValue placeholder="Select language" />
                    </SelectTrigger>
                    <SelectContent className={`${theme.colors.background.card} ${theme.colors.background.cardBorder}`}>
                      {languages.map((lang) => (
                        <SelectItem key={lang.value} value={lang.value} className={`${theme.colors.text.primary} hover:${theme.colors.chat.hover}`}>
                          {lang.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Button onClick={createRoom} className={`w-full ${theme.colors.interactive.button.primary}`}>
                    Create Room
                  </Button>
                </div>
              </DialogContent>
            </Dialog>

            <Dialog open={isJoinRoomOpen} onOpenChange={setIsJoinRoomOpen}>
              <DialogTrigger asChild>
                <Button className={`${theme.colors.interactive.button.secondary} ${theme.colors.text.primary} hover:scale-105 transform transition-all duration-200`}>
                  <Users className="w-4 h-4 mr-2" />
                  Join Room
                </Button>
              </DialogTrigger>
              <DialogContent className={`${theme.colors.background.card} ${theme.colors.background.cardBorder} ${theme.colors.glow.card}`}>
                <DialogHeader>
                  <DialogTitle className={theme.colors.text.primary}>Join Room</DialogTitle>
                </DialogHeader>
                <div className="space-y-4">
                  <Input
                    placeholder="Enter room ID"
                    value={joinRoomId}
                    onChange={(e) => setJoinRoomId(e.target.value)}
                    className={theme.colors.interactive.input}
                  />
                  <Button onClick={() => joinRoom()} className={`w-full ${theme.colors.interactive.button.primary}`}>
                    Join Room
                  </Button>
                </div>
              </DialogContent>
            </Dialog>
          </div>
        </div>

        {/* Status and Room Info */}
        <div className={`grid gap-4 mb-6 ${isInRoom ? 'grid-cols-1 lg:grid-cols-2' : 'grid-cols-1 lg:grid-cols-3'}`}>
          <Card className={`${theme.colors.background.card} ${theme.colors.background.cardBorder} ${theme.colors.glow.card} hover:scale-[1.02] transform transition-all duration-200`}>
            <CardHeader className="pb-3">
              <CardTitle className={`${theme.colors.text.primary} text-sm`}>Connection Status</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                <div className={`w-3 h-3 rounded-full ${isConnected ? theme.colors.status.online : theme.colors.status.offline}`}></div>
                <span className={`${theme.colors.text.secondary} text-sm`}>
                  {isConnected ? 'Connected' : 'Disconnected'}
                </span>
              </div>
            </CardContent>
          </Card>

          {isInRoom && (
            <Card className={`${theme.colors.background.card} ${theme.colors.background.cardBorder} ${theme.colors.glow.card} hover:scale-[1.02] transform transition-all duration-200`}>
              <CardHeader className="pb-3">
                <CardTitle className={`${theme.colors.text.primary} text-sm`}>Room Info</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className={`${theme.colors.text.secondary} text-sm`}>{roomName}</span>
                    <div className="flex items-center gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={copyRoomId}
                        className={`${theme.colors.text.accent} hover:${theme.colors.text.primary} p-1 hover:scale-110 transform transition-all duration-200`}
                      >
                        <Copy className="w-3 h-3" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setIsRoomDeletionOpen(true)}
                        className={`text-red-400 hover:text-red-300 p-1 hover:scale-110 transform transition-all duration-200`}
                      >
                        <Trash2 className="w-3 h-3" />
                      </Button>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <UserAvatar userName={userName} userId={userId} size="xs" />
                    <Badge variant="secondary" className={`text-xs ${theme.colors.background.glass} ${theme.colors.text.secondary}`}>
                      {userName || userId}
                    </Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Main Content - 3 Column Layout when in room */}
        {isInRoom ? (
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
            {/* Left Column - User List (Hidden on mobile) */}
            <div className="hidden lg:block">
              <Card className={`${theme.colors.background.card} ${theme.colors.background.cardBorder} ${theme.colors.glow.card} hover:scale-[1.02] transform transition-all duration-200`}>
                <CardHeader className="pb-3">
                  <CardTitle className={`${theme.colors.text.primary} text-sm flex items-center gap-2`}>
                    <Users className="w-4 h-4" />
                    Online ({connectedUsers.length})
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {connectedUsers.map((user) => (
                      <div key={user.user_id} className={`flex items-center gap-3 p-2 rounded-lg ${theme.colors.background.glass} hover:scale-105 transform transition-all duration-200`}>
                        <UserAvatar 
                          userName={user.user_name} 
                          userId={user.user_id} 
                          size="sm" 
                          isOnline={true} 
                        />
                        <span className={`${theme.colors.text.secondary} text-sm truncate flex-1`}>
                          {user.user_name || user.user_id}
                        </span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Center Column - Code Editor */}
            <div className="lg:col-span-2">
              <Card className={`${theme.colors.background.card} ${theme.colors.background.cardBorder} ${theme.colors.glow.card} hover:scale-[1.01] transform transition-all duration-200`}>
                <CardHeader>
                  <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                    {/* File Tabs */}
                    <div className="flex items-center gap-2 flex-wrap">
                      {openFiles.map((file) => (
                        <div key={file.id} className="flex items-center">
                          <button
                            onClick={() => switchToFile(file.id)}
                            className={`
                              flex items-center gap-2 px-3 py-1.5 rounded-t-lg text-sm transition-all duration-200
                              ${file.isActive 
                                ? `${theme.colors.interactive.button.accent} ${theme.colors.text.primary}` 
                                : `${theme.colors.background.glass} ${theme.colors.text.secondary} hover:${theme.colors.text.primary}`
                              }
                            `}
                          >
                            <FileText className="w-3 h-3" />
                            <span>{file.name}</span>
                            {openFiles.length > 1 && (
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  closeFile(file.id);
                                }}
                                className="ml-1 hover:bg-red-500/20 rounded p-0.5"
                              >
                                <X className="w-3 h-3" />
                              </button>
                            )}
                          </button>
                        </div>
                      ))}
                      <button
                        onClick={addNewFile}
                        className={`
                          flex items-center gap-1 px-2 py-1.5 rounded-lg text-sm transition-all duration-200
                          ${theme.colors.background.glass} ${theme.colors.text.muted}
                          hover:${theme.colors.text.secondary} hover:scale-105 transform
                        `}
                      >
                        <Plus className="w-3 h-3" />
                      </button>
                    </div>

                    <div className="flex items-center gap-4">
                      <Select value={language} onValueChange={handleLanguageChange}>
                        <SelectTrigger className={`w-40 ${theme.colors.interactive.select}`}>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent className={`${theme.colors.background.card} ${theme.colors.background.cardBorder}`}>
                          {languages.map((lang) => (
                            <SelectItem key={lang.value} value={lang.value} className={`${theme.colors.text.primary} hover:${theme.colors.chat.hover}`}>
                              {lang.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="flex gap-2">
                      <Button
                        onClick={runCode}
                        disabled={isCodeRunning}
                        className={`${theme.colors.interactive.button.primary} hover:scale-105 transform transition-all duration-200`}
                      >
                        <Play className="w-4 h-4 mr-2" />
                        {isCodeRunning ? 'Running...' : 'Run'}
                      </Button>
                      <Button
                        onClick={saveFile}
                        disabled={!isInRoom}
                        className={`${theme.colors.interactive.button.accent} hover:scale-105 transform transition-all duration-200`}
                      >
                        <Save className="w-4 h-4 mr-2" />
                        Save
                      </Button>
                      <Button
                        onClick={resetCode}
                        className={`${theme.colors.interactive.button.secondary} hover:scale-105 transform transition-all duration-200`}
                      >
                        <RotateCcw className="w-4 h-4 mr-2" />
                        Reset
                      </Button>
                      <Button
                        onClick={downloadFile}
                        className={`${theme.colors.interactive.button.secondary} hover:scale-105 transform transition-all duration-200`}
                      >
                        <Download className="w-4 h-4 mr-2" />
                        Download
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="p-0">
                  <div className="h-96 lg:h-[600px] border border-slate-600/30 rounded-lg overflow-hidden backdrop-blur-sm">
                    <MonacoEditor
                      height="100%"
                      language={language}
                      value={code}
                      onChange={handleCodeChange}
                      onMount={handleEditorDidMount}
                      theme="vs-dark"
                      options={{
                        fontSize: 14,
                        fontFamily: 'JetBrains Mono, Fira Code, monospace',
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
            </div>

            {/* Right Column - Chat Panel */}
            <div className={`${showChat ? 'block' : 'hidden'} lg:block`}>
              <Card className={`${theme.colors.background.card} ${theme.colors.background.cardBorder} ${theme.colors.glow.card} hover:scale-[1.02] transform transition-all duration-200`}>
                <CardHeader className="pb-3">
                  <div className="flex justify-between items-center">
                    <CardTitle className={`${theme.colors.text.primary} text-sm flex items-center gap-2`}>
                      <MessageCircle className="w-4 h-4" />
                      Chat
                    </CardTitle>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setShowChat(!showChat)}
                      className={`${theme.colors.text.muted} hover:${theme.colors.text.secondary} p-1 lg:hidden hover:scale-110 transform transition-all duration-200`}
                    >
                      {showChat ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
                    </Button>
                  </div>
                </CardHeader>
                <CardContent className="p-0">
                  {/* Chat Messages */}
                  <div className={`h-80 lg:h-[500px] overflow-y-auto p-3 space-y-3 ${theme.colors.background.glass} mx-3 mb-3 rounded backdrop-blur-sm`}>
                    {chatMessages.length === 0 ? (
                      <div className={`text-center ${theme.colors.text.muted} text-sm py-8`}>
                        No messages yet. Start a conversation!
                      </div>
                    ) : (
                      chatMessages.map((message) => (
                        <div key={message.id} className={`flex ${message.user_id === userId ? 'justify-end' : 'justify-start'}`}>
                          <div className="max-w-xs lg:max-w-sm">
                            <div className={`
                              p-3 rounded-lg transition-all duration-200 hover:scale-[1.02] transform
                              ${message.user_id === userId 
                                ? theme.colors.chat.own
                                : theme.colors.chat.other
                              }
                            `}>
                              {message.user_id !== userId && (
                                <div className="flex items-center gap-2 mb-2">
                                  <UserAvatar 
                                    userName={message.user_name} 
                                    userId={message.user_id} 
                                    size="xs" 
                                  />
                                  <div className={`text-xs font-medium ${theme.colors.text.accent}`}>
                                    {message.user_name}
                                  </div>
                                </div>
                              )}
                              <div className="text-sm whitespace-pre-wrap">{message.message}</div>
                              <div className={`text-xs ${theme.colors.text.muted} mt-2 flex justify-between items-center`}>
                                <span>
                                  {new Date(message.timestamp).toLocaleTimeString([], { 
                                    hour: '2-digit', 
                                    minute: '2-digit' 
                                  })}
                                </span>
                              </div>
                            </div>
                            <EmojiReaction
                              messageId={message.id}
                              reactions={messageReactions[message.id] || []}
                              onReact={handleMessageReaction}
                              currentUserId={userId}
                            />
                          </div>
                        </div>
                      ))
                    )}
                    <div ref={chatEndRef} />
                  </div>
                  
                  {/* Chat Input */}
                  <div className={`p-3 border-t ${theme.colors.background.cardBorder}`}>
                    <div className="flex gap-2">
                      <Input
                        value={newChatMessage}
                        onChange={(e) => setNewChatMessage(e.target.value)}
                        onKeyPress={handleChatKeyPress}
                        placeholder="Type a message..."
                        disabled={isSendingMessage}
                        className={`${theme.colors.interactive.input} flex-1`}
                        maxLength={200}
                      />
                      <Button
                        onClick={sendChatMessage}
                        disabled={isSendingMessage || !newChatMessage.trim()}
                        size="sm"
                        className={`${theme.colors.interactive.button.accent} hover:scale-105 transform transition-all duration-200`}
                      >
                        <Send className="w-4 h-4" />
                      </Button>
                    </div>
                    <div className={`text-xs ${theme.colors.text.muted} mt-1`}>
                      {newChatMessage.length}/200 characters
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        ) : (
          /* Single Column Layout when not in room */
          <Card className={`${theme.colors.background.card} ${theme.colors.background.cardBorder} ${theme.colors.glow.card} hover:scale-[1.01] transform transition-all duration-200`}>
            <CardHeader>
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                <div className="flex items-center gap-4">
                  <Select value={language} onValueChange={handleLanguageChange}>
                    <SelectTrigger className={`w-40 ${theme.colors.interactive.select}`}>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className={`${theme.colors.background.card} ${theme.colors.background.cardBorder}`}>
                      {languages.map((lang) => (
                        <SelectItem key={lang.value} value={lang.value} className={`${theme.colors.text.primary} hover:${theme.colors.chat.hover}`}>
                          {lang.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="flex gap-2">
                  <Button
                    onClick={runCode}
                    disabled={isCodeRunning}
                    className={`${theme.colors.interactive.button.primary} hover:scale-105 transform transition-all duration-200`}
                  >
                    <Play className="w-4 h-4 mr-2" />
                    {isCodeRunning ? 'Running...' : 'Run'}
                  </Button>
                  <Button
                    onClick={resetCode}
                    className={`${theme.colors.interactive.button.secondary} hover:scale-105 transform transition-all duration-200`}
                  >
                    <RotateCcw className="w-4 h-4 mr-2" />
                    Reset
                  </Button>
                  <Button
                    onClick={downloadFile}
                    className={`${theme.colors.interactive.button.secondary} hover:scale-105 transform transition-all duration-200`}
                  >
                    <Download className="w-4 h-4 mr-2" />
                    Download
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent className="p-0">
              <div className="h-96 lg:h-[600px] border border-slate-600/30 rounded-lg overflow-hidden backdrop-blur-sm">
                <MonacoEditor
                  height="100%"
                  language={language}
                  value={code}
                  onChange={handleCodeChange}
                  onMount={handleEditorDidMount}
                  theme="vs-dark"
                  options={{
                    fontSize: 14,
                    fontFamily: 'JetBrains Mono, Fira Code, monospace',
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
        )}

        {/* Output Console */}
        {showOutput && (
          <div className="mt-4">
            <Card className={`${theme.colors.background.card} ${theme.colors.background.cardBorder} ${theme.colors.glow.card} hover:scale-[1.02] transform transition-all duration-200`}>
              <CardHeader className="pb-3">
                <div className="flex justify-between items-center">
                  <CardTitle className={`${theme.colors.text.primary} text-sm flex items-center gap-2`}>
                    <Code className="w-4 h-4" />
                    Output Console
                  </CardTitle>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setShowOutput(false)}
                    className={`${theme.colors.text.muted} hover:${theme.colors.text.secondary} p-1 hover:scale-110 transform transition-all duration-200`}
                  >
                    <X className="w-4 h-4" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className={`${theme.colors.background.glass} rounded p-4 font-mono text-sm max-h-60 overflow-y-auto backdrop-blur-sm`}>
                  {codeOutput.stdout && (
                    <div className="text-green-400 mb-2">
                      <strong>Output:</strong>
                      <pre className="whitespace-pre-wrap mt-1">{codeOutput.stdout}</pre>
                    </div>
                  )}
                  {codeOutput.stderr && (
                    <div className="text-red-400 mb-2">
                      <strong>Error:</strong>
                      <pre className="whitespace-pre-wrap mt-1">{codeOutput.stderr}</pre>
                    </div>
                  )}
                  <div className={`${theme.colors.text.muted} text-xs mt-2`}>
                    Exit code: {codeOutput.exit_code}
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* User Name Prompt Dialog */}
        <Dialog open={isUserNamePromptOpen} onOpenChange={setIsUserNamePromptOpen}>
          <DialogContent className={`${theme.colors.background.card} ${theme.colors.background.cardBorder} ${theme.colors.glow.card}`}>
            <DialogHeader>
              <DialogTitle className={theme.colors.text.primary}>Enter Your Display Name</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Input
                  placeholder="Enter your display name (3-15 characters)"
                  value={tempUserName}
                  onChange={(e) => {
                    setTempUserName(e.target.value);
                    setUserNameError('');
                  }}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      handleUserNameSubmit();
                    }
                  }}
                  className={theme.colors.interactive.input}
                />
                {userNameError && (
                  <p className="text-red-400 text-sm mt-1">{userNameError}</p>
                )}
                <p className={`${theme.colors.text.muted} text-xs mt-1`}>
                  Only letters, numbers, and underscores allowed
                </p>
              </div>
              <Button onClick={handleUserNameSubmit} className={`w-full ${theme.colors.interactive.button.primary}`}>
                Continue
              </Button>
            </div>
          </DialogContent>
        </Dialog>

        {/* Room Deletion Dialog */}
        <RoomDeletion
          isOpen={isRoomDeletionOpen}
          onClose={() => setIsRoomDeletionOpen(false)}
          roomName={roomName}
          openFiles={openFiles}
          onDeleteConfirm={handleRoomDeletion}
        />

        {/* Status Message */}
        {statusMessage && (
          <div className="mt-4">
            <Card className={`${theme.colors.background.glass} ${theme.colors.background.cardBorder} hover:scale-[1.02] transform transition-all duration-200`}>
              <CardContent className="py-3">
                <p className={`${theme.colors.text.secondary} text-sm`}>{statusMessage}</p>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}

function App() {
  return (
    <ThemeProvider>
      <AppContent />
    </ThemeProvider>
  );
}

export default App;
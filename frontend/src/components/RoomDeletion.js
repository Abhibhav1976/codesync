import React, { useState } from 'react';
import { useTheme } from '../contexts/ThemeContext';
import { Trash2, Download, AlertTriangle, X } from 'lucide-react';
import { Button } from './ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import JSZip from 'jszip';
import { saveAs } from 'file-saver';

const RoomDeletion = ({ isOpen, onClose, roomName, openFiles, onDeleteConfirm }) => {
  const { theme } = useTheme();
  const [isDownloading, setIsDownloading] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  const downloadFilesAsZip = async () => {
    setIsDownloading(true);
    try {
      const zip = new JSZip();
      
      // Add each open file to the zip
      openFiles.forEach(file => {
        const fileName = file.name || `untitled.${getFileExtension(file.language)}`;
        zip.file(fileName, file.content || '');
      });
      
      // Generate the zip file
      const content = await zip.generateAsync({ type: 'blob' });
      
      // Download the zip file
      const roomNameSafe = roomName.replace(/[^a-z0-9]/gi, '_').toLowerCase();
      saveAs(content, `${roomNameSafe}_code_files.zip`);
      
      return true;
    } catch (error) {
      console.error('Error creating zip file:', error);
      return false;
    } finally {
      setIsDownloading(false);
    }
  };

  const getFileExtension = (language) => {
    switch (language) {
      case 'javascript': return 'js';
      case 'python': return 'py';
      case 'cpp': return 'cpp';
      case 'typescript': return 'ts';
      case 'html': return 'html';
      case 'css': return 'css';
      default: return 'txt';
    }
  };

  const handleDownloadAndDelete = async () => {
    const downloadSuccess = await downloadFilesAsZip();
    if (downloadSuccess) {
      handleDeleteOnly();
    }
  };

  const handleDeleteOnly = () => {
    setIsDeleting(true);
    // Simulate deletion process
    setTimeout(() => {
      onDeleteConfirm();
      setIsDeleting(false);
      onClose();
    }, 1000);
  };

  if (!isOpen) return null;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className={`${theme.colors.background.card} ${theme.colors.background.cardBorder} ${theme.colors.glow.card} max-w-md`}>
        <DialogHeader>
          <DialogTitle className={`${theme.colors.text.primary} flex items-center gap-2`}>
            <AlertTriangle className="w-5 h-5 text-red-500" />
            Delete Room
          </DialogTitle>
        </DialogHeader>
        
        <div className="space-y-4">
          <div className={`${theme.colors.text.secondary} text-sm`}>
            <p className="mb-2">
              Are you sure you want to delete <strong className={theme.colors.text.primary}>"{roomName}"</strong>?
            </p>
            <p className={theme.colors.text.muted}>
              This action cannot be undone. All room data and chat history will be permanently deleted.
            </p>
          </div>

          {openFiles && openFiles.length > 0 && (
            <div className={`${theme.colors.background.glass} p-3 rounded-lg`}>
              <p className={`${theme.colors.text.secondary} text-sm mb-2`}>
                📝 Would you like to download your code files before deleting?
              </p>
              <div className={`${theme.colors.text.muted} text-xs`}>
                Files to download: {openFiles.map(f => f.name).join(', ')}
              </div>
            </div>
          )}

          <div className="flex flex-col gap-2">
            <Button
              onClick={handleDownloadAndDelete}
              disabled={isDownloading || isDeleting}
              className={`w-full ${theme.colors.interactive.button.accent} hover:scale-105 transform transition-all duration-200`}
            >
              <Download className="w-4 h-4 mr-2" />
              {isDownloading ? 'Downloading...' : 'Yes, Download & Delete'}
            </Button>
            
            <Button
              onClick={handleDeleteOnly}
              disabled={isDownloading || isDeleting}
              variant="destructive"
              className={`w-full bg-red-600 hover:bg-red-700 text-white hover:scale-105 transform transition-all duration-200`}
            >
              <Trash2 className="w-4 h-4 mr-2" />
              {isDeleting ? 'Deleting...' : 'Delete Without Download'}
            </Button>
            
            <Button
              onClick={onClose}
              disabled={isDownloading || isDeleting}
              className={`w-full ${theme.colors.interactive.button.secondary} hover:scale-105 transform transition-all duration-200`}
            >
              <X className="w-4 h-4 mr-2" />
              Cancel
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default RoomDeletion;
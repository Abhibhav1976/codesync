import React from 'react';
import { useTheme } from '../contexts/ThemeContext';

const UserAvatar = ({ userName, userId, size = 'sm', isOnline = true }) => {
  const { theme } = useTheme();
  
  // Generate consistent colors based on user ID
  const generateAvatarColor = (id) => {
    const colors = [
      'from-purple-500 to-purple-600',
      'from-blue-500 to-blue-600',
      'from-green-500 to-green-600',
      'from-yellow-500 to-yellow-600',
      'from-pink-500 to-pink-600',
      'from-indigo-500 to-indigo-600',
      'from-red-500 to-red-600',
      'from-teal-500 to-teal-600',
    ];
    const hash = id.split('').reduce((a, b) => {
      a = ((a << 5) - a) + b.charCodeAt(0);
      return a & a;
    }, 0);
    return colors[Math.abs(hash) % colors.length];
  };

  const sizeClasses = {
    xs: 'w-6 h-6 text-xs',
    sm: 'w-8 h-8 text-sm',
    md: 'w-10 h-10 text-base',
    lg: 'w-12 h-12 text-lg',
  };

  const getInitials = (name) => {
    if (!name) return '?';
    return name.split(' ').map(word => word[0]).join('').toUpperCase().slice(0, 2);
  };

  return (
    <div className="relative">
      <div className={`
        ${sizeClasses[size]}
        rounded-full
        bg-gradient-to-br ${generateAvatarColor(userId)}
        flex items-center justify-center
        font-bold text-white
        shadow-lg
        border-2 border-white/20
        transition-all duration-200
        hover:scale-110 transform
      `}>
        {getInitials(userName || userId)}
      </div>
      
      {/* Online status indicator */}
      <div className={`
        absolute -bottom-0.5 -right-0.5
        w-3 h-3 rounded-full border-2 border-white
        ${isOnline ? theme.colors.status.online : theme.colors.status.offline}
        transition-all duration-200
      `} />
    </div>
  );
};

export default UserAvatar;
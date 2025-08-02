import React, { createContext, useContext, useState, useEffect } from 'react';

const ThemeContext = createContext();

export const themes = {
  darkPurple: {
    name: 'Dark Purple',
    id: 'darkPurple',
    colors: {
      // Main background gradients
      background: {
        primary: 'from-slate-900 via-purple-900 to-slate-900',
        secondary: 'from-slate-800 via-purple-800 to-slate-800',
        card: 'bg-slate-800/70 backdrop-blur-xl',
        cardBorder: 'border-slate-700/50',
        glass: 'bg-slate-800/20 backdrop-blur-md border border-slate-700/30',
      },
      // Text colors
      text: {
        primary: 'text-white',
        secondary: 'text-slate-300',
        muted: 'text-slate-400',
        accent: 'text-purple-400',
      },
      // Interactive elements
      interactive: {
        button: {
          primary: 'bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 shadow-lg shadow-purple-500/25',
          secondary: 'bg-slate-700/50 hover:bg-slate-600/50 border border-slate-600/50 backdrop-blur-sm',
          accent: 'bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 shadow-lg shadow-blue-500/25',
        },
        input: 'bg-slate-700/50 border-slate-600/50 text-white placeholder-slate-400 backdrop-blur-sm',
        select: 'bg-slate-700/50 border-slate-600/50 text-white backdrop-blur-sm',
      },
      // Status indicators
      status: {
        online: 'bg-green-500 shadow-lg shadow-green-500/50',
        offline: 'bg-red-500 shadow-lg shadow-red-500/50',
        typing: 'bg-yellow-500 shadow-lg shadow-yellow-500/50',
      },
      // Chat specific
      chat: {
        own: 'bg-gradient-to-r from-blue-600/80 to-blue-700/80 backdrop-blur-sm border border-blue-500/30',
        other: 'bg-slate-700/60 backdrop-blur-sm border border-slate-600/30',
        hover: 'hover:bg-slate-600/70',
      },
      // Glow effects
      glow: {
        primary: 'shadow-2xl shadow-purple-500/20',
        accent: 'shadow-2xl shadow-blue-500/20',
        card: 'shadow-xl shadow-slate-900/50',
      }
    }
  },
  
  light: {
    name: 'Light Mode',
    id: 'light',
    colors: {
      background: {
        primary: 'from-slate-50 via-blue-50 to-slate-50',
        secondary: 'from-slate-100 via-blue-100 to-slate-100',
        card: 'bg-white/80 backdrop-blur-xl',
        cardBorder: 'border-slate-200/60',
        glass: 'bg-white/40 backdrop-blur-md border border-slate-200/50',
      },
      text: {
        primary: 'text-slate-900',
        secondary: 'text-slate-700',
        muted: 'text-slate-500',
        accent: 'text-blue-600',
      },
      interactive: {
        button: {
          primary: 'bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 shadow-lg shadow-blue-500/25 text-white',
          secondary: 'bg-white/60 hover:bg-white/80 border border-slate-300/50 backdrop-blur-sm text-slate-700',
          accent: 'bg-gradient-to-r from-purple-500 to-purple-600 hover:from-purple-600 hover:to-purple-700 shadow-lg shadow-purple-500/25 text-white',
        },
        input: 'bg-white/60 border-slate-300/50 text-slate-900 placeholder-slate-500 backdrop-blur-sm',
        select: 'bg-white/60 border-slate-300/50 text-slate-900 backdrop-blur-sm',
      },
      status: {
        online: 'bg-green-500 shadow-lg shadow-green-500/50',
        offline: 'bg-red-500 shadow-lg shadow-red-500/50',
        typing: 'bg-amber-500 shadow-lg shadow-amber-500/50',
      },
      chat: {
        own: 'bg-gradient-to-r from-blue-500/20 to-blue-600/20 backdrop-blur-sm border border-blue-400/30 text-slate-900',
        other: 'bg-white/70 backdrop-blur-sm border border-slate-300/40 text-slate-900',
        hover: 'hover:bg-white/90',
      },
      glow: {
        primary: 'shadow-2xl shadow-blue-500/15',
        accent: 'shadow-2xl shadow-purple-500/15',
        card: 'shadow-xl shadow-slate-200/80',
      }
    }
  },
  
  redMaroon: {
    name: 'Red Maroon',
    id: 'redMaroon',
    colors: {
      background: {
        primary: 'from-slate-900 via-red-950 to-slate-900',
        secondary: 'from-red-900 via-red-800 to-red-900',
        card: 'bg-red-950/70 backdrop-blur-xl',
        cardBorder: 'border-red-800/50',
        glass: 'bg-red-950/20 backdrop-blur-md border border-red-800/30',
      },
      text: {
        primary: 'text-white',
        secondary: 'text-red-100',
        muted: 'text-red-300',
        accent: 'text-red-400',
      },
      interactive: {
        button: {
          primary: 'bg-gradient-to-r from-red-600 to-red-700 hover:from-red-700 hover:to-red-800 shadow-lg shadow-red-500/25',
          secondary: 'bg-red-900/50 hover:bg-red-800/50 border border-red-700/50 backdrop-blur-sm',
          accent: 'bg-gradient-to-r from-orange-600 to-orange-700 hover:from-orange-700 hover:to-orange-800 shadow-lg shadow-orange-500/25',
        },
        input: 'bg-red-900/50 border-red-700/50 text-white placeholder-red-400 backdrop-blur-sm',
        select: 'bg-red-900/50 border-red-700/50 text-white backdrop-blur-sm',
      },
      status: {
        online: 'bg-green-500 shadow-lg shadow-green-500/50',
        offline: 'bg-red-500 shadow-lg shadow-red-500/50',
        typing: 'bg-orange-500 shadow-lg shadow-orange-500/50',
      },
      chat: {
        own: 'bg-gradient-to-r from-orange-600/80 to-orange-700/80 backdrop-blur-sm border border-orange-500/30',
        other: 'bg-red-900/60 backdrop-blur-sm border border-red-700/30',
        hover: 'hover:bg-red-800/70',
      },
      glow: {
        primary: 'shadow-2xl shadow-red-500/20',
        accent: 'shadow-2xl shadow-orange-500/20',
        card: 'shadow-xl shadow-red-950/50',
      }
    }
  }
};

export const ThemeProvider = ({ children }) => {
  const [currentTheme, setCurrentTheme] = useState(() => {
    const saved = localStorage.getItem('editorTheme');
    return saved && themes[saved] ? saved : 'darkPurple';
  });

  useEffect(() => {
    localStorage.setItem('editorTheme', currentTheme);
  }, [currentTheme]);

  const switchTheme = (themeId) => {
    if (themes[themeId]) {
      setCurrentTheme(themeId);
    }
  };

  const theme = themes[currentTheme];

  return (
    <ThemeContext.Provider value={{ theme, currentTheme, switchTheme, themes }}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};
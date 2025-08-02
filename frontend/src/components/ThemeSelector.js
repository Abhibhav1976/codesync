import React, { useState } from 'react';
import { useTheme } from '../contexts/ThemeContext';
import { ChevronDown, Palette } from 'lucide-react';

const ThemeSelector = () => {
  const { theme, currentTheme, switchTheme, themes } = useTheme();
  const [isOpen, setIsOpen] = useState(false);

  const handleThemeChange = (themeId) => {
    switchTheme(themeId);
    setIsOpen(false);
  };

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`
          flex items-center gap-2 px-3 py-2 rounded-lg transition-all duration-200
          ${theme.colors.interactive.button.secondary}
          ${theme.colors.text.primary}
          hover:scale-105 transform
          ${theme.colors.glow.accent}
        `}
      >
        <Palette className="w-4 h-4" />
        <span className="text-sm font-medium hidden sm:inline">{theme.name}</span>
        <ChevronDown className={`w-4 h-4 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-40"
            onClick={() => setIsOpen(false)}
          />
          
          {/* Dropdown */}
          <div className={`
            absolute right-0 top-12 z-50 min-w-48 rounded-lg overflow-hidden
            ${theme.colors.background.glass}
            ${theme.colors.glow.card}
            border backdrop-blur-xl
            ${theme.colors.background.cardBorder}
          `}>
            {Object.values(themes).map((themeOption) => (
              <button
                key={themeOption.id}
                onClick={() => handleThemeChange(themeOption.id)}
                className={`
                  w-full px-4 py-3 text-left transition-all duration-200
                  flex items-center gap-3
                  ${currentTheme === themeOption.id 
                    ? `${theme.colors.chat.own} ${theme.colors.text.primary}` 
                    : `${theme.colors.chat.hover} ${theme.colors.text.secondary}`
                  }
                  hover:scale-[1.02] transform
                `}
              >
                <div className={`
                  w-4 h-4 rounded-full
                  ${themeOption.id === 'darkPurple' ? 'bg-gradient-to-r from-purple-600 to-purple-700' : ''}
                  ${themeOption.id === 'light' ? 'bg-gradient-to-r from-blue-500 to-blue-600' : ''}
                  ${themeOption.id === 'redMaroon' ? 'bg-gradient-to-r from-red-600 to-red-700' : ''}
                  shadow-lg
                `} />
                <span className="font-medium">{themeOption.name}</span>
                {currentTheme === themeOption.id && (
                  <div className={`ml-auto w-2 h-2 rounded-full ${theme.colors.status.online}`} />
                )}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
};

export default ThemeSelector;
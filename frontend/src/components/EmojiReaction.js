import React, { useState } from 'react';
import { useTheme } from '../contexts/ThemeContext';
import { Smile, Heart, ThumbsUp, Laugh, Zap, Angry } from 'lucide-react';

const EmojiReaction = ({ messageId, reactions = [], onReact, currentUserId }) => {
  const { theme } = useTheme();
  const [showPicker, setShowPicker] = useState(false);

  const defaultEmojis = [
    { emoji: '👍', icon: ThumbsUp, name: 'thumbsup' },
    { emoji: '❤️', icon: Heart, name: 'heart' },
    { emoji: '😂', icon: Laugh, name: 'laugh' },
    { emoji: '⚡', icon: Zap, name: 'zap' },
    { emoji: '😢', name: 'sad' },
    { emoji: '😡', icon: Angry, name: 'angry' },
  ];

  const handleReaction = (reactionName) => {
    onReact(messageId, reactionName);
    setShowPicker(false);
  };

  const getReactionCount = (reactionName) => {
    return reactions.filter(r => r.type === reactionName).length;
  };

  const hasUserReacted = (reactionName) => {
    return reactions.some(r => r.type === reactionName && r.userId === currentUserId);
  };

  const getUniqueReactions = () => {
    const reactionCounts = {};
    reactions.forEach(reaction => {
      if (!reactionCounts[reaction.type]) {
        reactionCounts[reaction.type] = {
          type: reaction.type,
          count: 0,
          users: [],
          hasCurrentUser: false
        };
      }
      reactionCounts[reaction.type].count++;
      reactionCounts[reaction.type].users.push(reaction.userId);
      if (reaction.userId === currentUserId) {
        reactionCounts[reaction.type].hasCurrentUser = true;
      }
    });
    return Object.values(reactionCounts);
  };

  return (
    <div className="relative">
      <div className="flex items-center gap-1 mt-1">
        {/* Existing reactions */}
        {getUniqueReactions().map((reaction) => {
          const emojiData = defaultEmojis.find(e => e.name === reaction.type);
          return (
            <button
              key={reaction.type}
              onClick={() => handleReaction(reaction.type)}
              className={`
                flex items-center gap-1 px-2 py-1 rounded-full text-xs
                transition-all duration-200 hover:scale-105 transform
                ${reaction.hasCurrentUser 
                  ? `${theme.colors.interactive.button.accent} ${theme.colors.text.primary}` 
                  : `${theme.colors.background.glass} ${theme.colors.text.muted} hover:${theme.colors.text.secondary}`
                }
              `}
              title={`${reaction.users.join(', ')} reacted with ${reaction.type}`}
            >
              <span>{emojiData?.emoji || '👍'}</span>
              <span>{reaction.count}</span>
            </button>
          );
        })}

        {/* Add reaction button */}
        <button
          onClick={() => setShowPicker(!showPicker)}
          className={`
            w-6 h-6 rounded-full flex items-center justify-center
            ${theme.colors.background.glass}
            ${theme.colors.text.muted}
            hover:${theme.colors.text.secondary}
            transition-all duration-200 hover:scale-110 transform
          `}
        >
          <Smile className="w-3 h-3" />
        </button>
      </div>

      {/* Emoji picker */}
      {showPicker && (
        <>
          <div
            className="fixed inset-0 z-40"
            onClick={() => setShowPicker(false)}
          />
          <div className={`
            absolute bottom-8 left-0 z-50 p-2 rounded-lg
            ${theme.colors.background.glass}
            ${theme.colors.glow.card}
            border backdrop-blur-xl
            ${theme.colors.background.cardBorder}
            flex gap-1
          `}>
            {defaultEmojis.map((emojiData) => (
              <button
                key={emojiData.name}
                onClick={() => handleReaction(emojiData.name)}
                className={`
                  w-8 h-8 rounded-lg flex items-center justify-center
                  ${theme.colors.chat.hover}
                  transition-all duration-200 hover:scale-125 transform
                `}
                title={emojiData.name}
              >
                {emojiData.emoji}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
};

export default EmojiReaction;
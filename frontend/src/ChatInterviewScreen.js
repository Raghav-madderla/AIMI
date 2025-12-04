import React, { useState, useRef, useEffect } from 'react';

function ChatInterviewScreen({ messages, onSendMessage, isLoading, isDarkMode, currentQuestion, user }) {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef(null);

  // Get user initials from name or email
  const getUserInitials = () => {
    if (!user) return 'U';
    if (user.name) {
      const names = user.name.trim().split(' ');
      if (names.length >= 2) {
        return (names[0][0] + names[names.length - 1][0]).toUpperCase();
      }
      return names[0][0].toUpperCase();
    }
    if (user.email) {
      return user.email[0].toUpperCase();
    }
    return 'U';
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim() && !isLoading) {
      onSendMessage(input);
      setInput('');
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  // Auto-resize textarea
  const textareaRef = useRef(null);
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = '52px';
      textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`;
    }
  }, [input]);

  const styles = {
    container: {
      display: 'flex',
      flexDirection: 'column',
      height: 'calc(100vh - 72px)',
      backgroundColor: isDarkMode ? '#0f0f0f' : '#ffffff',
      fontFamily: 'Inter, sans-serif',
    },
    messagesContainer: {
      flex: 1,
      overflowY: 'auto',
      padding: '1.75rem',
      display: 'flex',
      flexDirection: 'column',
      gap: '1.25rem',
      maxWidth: '1200px',
      margin: '0 auto',
      width: '100%',
    },
    messageWrapper: {
      display: 'flex',
      width: '100%',
      marginBottom: '0.5rem',
    },
    messageWrapperAI: {
      justifyContent: 'flex-start',
    },
    messageWrapperUser: {
      justifyContent: 'flex-end',
    },
    message: {
      display: 'flex',
      gap: '0.75rem',
      maxWidth: '85%',
      alignItems: 'flex-start',
    },
    messageAI: {
      flexDirection: 'row',
    },
    messageUser: {
      flexDirection: 'row-reverse',
    },
    avatar: {
      width: '36px',
      height: '36px',
      borderRadius: '8px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      fontSize: '0.75rem',
      fontWeight: '700',
      flexShrink: 0,
      boxShadow: isDarkMode ? '0 2px 4px rgba(0, 0, 0, 0.3)' : '0 2px 4px rgba(0, 0, 0, 0.1)',
      backgroundColor: isDarkMode ? '#141414' : '#141414',
      border: `1px solid ${isDarkMode ? '#1f1f1f' : '#1f1f1f'}`,
    },
    avatarAI: {
      boxShadow: '0 4px 12px rgba(102, 126, 234, 0.35)',
    },
    avatarUser: {
      background: isDarkMode ? '#2d2d2d' : '#ffffff',
      color: isDarkMode ? '#ffffff' : '#000000',
      border: `1px solid ${isDarkMode ? '#3d3d3d' : '#e5e5e5'}`,
    },
    messageContent: {
      display: 'flex',
      flexDirection: 'column',
      gap: '0.25rem',
      alignItems: 'stretch',
      width: '100%',
    },
    messageBubble: {
      padding: '0.75rem 1rem',
      borderRadius: '12px',
      lineHeight: '1.55',
      fontSize: '0.875rem',
      fontWeight: '400',
      letterSpacing: '-0.005em',
      whiteSpace: 'pre-wrap',
      wordBreak: 'break-word',
      textAlign: 'left',
      boxShadow: isDarkMode ? '0 1px 2px rgba(0, 0, 0, 0.2)' : '0 1px 2px rgba(0, 0, 0, 0.05)',
      maxWidth: 'min(640px, 100%)',
    },
    messageBubbleUser: {
      backgroundColor: isDarkMode ? '#2d2d2d' : '#ffffff',
      color: isDarkMode ? '#ffffff' : '#000000',
      border: `1px solid ${isDarkMode ? '#3d3d3d' : '#e5e5e5'}`,
      borderTopRightRadius: '4px',
      alignSelf: 'flex-end',
    },
    messageAIPanel: {
      fontSize: '0.875rem',
      lineHeight: '1.6',
      color: isDarkMode ? '#e4e4e7' : '#1f2937',
      letterSpacing: '-0.005em',
      whiteSpace: 'pre-wrap',
      wordBreak: 'break-word',
      padding: '0.25rem 0',
      textAlign: 'left',
    },
    inputContainer: {
      padding: '1.695rem 1.5rem 1.25rem',
      borderTop: `1px solid ${isDarkMode ? '#2d2d2d' : '#e5e5e5'}`,
      backgroundColor: isDarkMode ? '#0f0f0f' : '#ffffff',
    },
    inputWrapper: {
      maxWidth: '1200px',
      margin: '0 auto',
      display: 'flex',
      gap: '0.75rem',
      alignItems: 'flex-start',
      padding: '0 1.5rem',
    },
    textarea: {
      flex: 1,
      minHeight: '76px',
      maxHeight: '200px',
      padding: '0.65rem 0.9rem',
      fontSize: '0.875rem',
      fontWeight: '400',
      borderRadius: '12px',
      border: `1px solid ${isDarkMode ? '#565869' : '#d1d5db'}`,
      backgroundColor: isDarkMode ? '#40414f' : '#ffffff',
      color: isDarkMode ? '#ececf1' : '#353740',
      fontFamily: 'Inter, sans-serif',
      resize: 'none',
      outline: 'none',
      transition: 'border-color 0.2s ease',
    },
    textareaFocus: {
      borderColor: isDarkMode ? '#5d5d5d' : '#9ca3af',
      boxShadow: isDarkMode ? '0 0 0 2px rgba(93, 93, 93, 0.2)' : '0 0 0 2px rgba(156, 163, 175, 0.1)',
    },
    sendButton: {
      width: '32px',
      height: '32px',
      borderRadius: '6px',
      border: `1px solid ${isDarkMode ? '#3d3d3d' : '#e5e5e5'}`,
      backgroundColor: isDarkMode ? '#2d2d2d' : '#ffffff',
      color: isDarkMode ? '#ffffff' : '#000000',
      cursor: 'pointer',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      transition: 'all 0.2s ease',
      flexShrink: 0,
      fontSize: '0.8125rem',
    },
    sendButtonDisabled: {
      backgroundColor: isDarkMode ? '#40414f' : '#d1d5db',
      cursor: 'not-allowed',
    },
    loadingDots: {
      display: 'inline-flex',
      gap: '4px',
      alignItems: 'center',
    },
    dot: {
      width: '6px',
      height: '6px',
      borderRadius: '50%',
      backgroundColor: isDarkMode ? '#ececf1' : '#353740',
      animation: 'bounce 1.4s infinite ease-in-out',
    },
    avatarLogoText: {
      fontSize: '0.875rem',
      fontWeight: '700',
      letterSpacing: '-0.02em',
      backgroundImage: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      WebkitBackgroundClip: 'text',
      backgroundClip: 'text',
      WebkitTextFillColor: 'transparent',
      color: 'transparent',
    },
  };

  return (
    <div style={styles.container}>
      <div style={styles.messagesContainer}>
        {messages.map((msg, idx) => (
          <div 
            key={idx} 
            style={{ 
              ...styles.messageWrapper, 
              ...(msg.role === 'user' ? styles.messageWrapperUser : styles.messageWrapperAI) 
            }}
          >
            <div style={{ 
              ...styles.message, 
              ...(msg.role === 'user' ? styles.messageUser : styles.messageAI) 
            }}>
              <div style={{ 
                ...styles.avatar, 
                ...(msg.role === 'user' ? styles.avatarUser : styles.avatarAI) 
              }}>
                {msg.role === 'user' ? getUserInitials() : (
                  <span style={styles.avatarLogoText}>AIMI</span>
                )}
              </div>
              <div style={styles.messageContent}>
                {msg.role === 'user' ? (
                  <div style={{ 
                    ...styles.messageBubble, 
                    ...styles.messageBubbleUser 
                  }}>
                    {msg.content}
                  </div>
                ) : (
                  <div style={styles.messageAIPanel}>
                    {msg.content}
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
        {isLoading && (
          <div style={{ ...styles.messageWrapper, ...styles.messageWrapperAI }}>
            <div style={{ ...styles.message, ...styles.messageAI }}>
              <div style={{ ...styles.avatar, ...styles.avatarAI }}>
                <span style={styles.avatarLogoText}>AIMI</span>
              </div>
              <div style={styles.messageContent}>
                <div style={styles.messageAIPanel}>
                  <div style={styles.loadingDots}>
                    <div style={{ ...styles.dot, animationDelay: '0s' }}></div>
                    <div style={{ ...styles.dot, animationDelay: '0.2s' }}></div>
                    <div style={{ ...styles.dot, animationDelay: '0.4s' }}></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      <div style={styles.inputContainer}>
        <form onSubmit={handleSubmit} style={styles.inputWrapper}>
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={currentQuestion ? "Type your answer..." : "Type your response..."}
            disabled={isLoading}
            style={styles.textarea}
            rows={1}
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            style={{
              ...styles.sendButton,
              ...((!input.trim() || isLoading) ? styles.sendButtonDisabled : {}),
            }}
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M.5 1.163A1 1 0 0 1 1.97.28l12.868 6.837a1 1 0 0 1 0 1.766L1.969 15.72A1 1 0 0 1 .5 14.836V10.33a1 1 0 0 1 .816-.983L8.5 8 1.316 6.653A1 1 0 0 1 .5 5.67V1.163Z" fill="currentColor"/>
            </svg>
          </button>
        </form>
      </div>
    </div>
  );
}

export default ChatInterviewScreen;


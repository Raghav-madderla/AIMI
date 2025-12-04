import React, { useState } from 'react';

function Sidebar({ chatSessions, currentSessionId, onSelectSession, onNewChat, isDarkMode, isOpen, onClose, user, onLogout, onDeleteSession }) {
  const getUserInitials = () => {
    if (!user) return 'U';
    if (user.name) {
      const parts = user.name.trim().split(' ');
      if (parts.length >= 2) {
        return `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase();
      }
      return parts[0][0].toUpperCase();
    }
    if (user.email) {
      return user.email[0].toUpperCase();
    }
    return 'U';
  };

  const [isNewChatHovered, setIsNewChatHovered] = useState(false);
  const [isLogoutHovered, setIsLogoutHovered] = useState(false);
  const [hoveredSessionId, setHoveredSessionId] = useState(null);
  const [openMenuSessionId, setOpenMenuSessionId] = useState(null);
  const [hoveredMenuButtonId, setHoveredMenuButtonId] = useState(null);
  const [hoveredMenuItemId, setHoveredMenuItemId] = useState(null);

  const styles = {
    overlay: {
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.5)',
      zIndex: 998,
      display: isOpen ? 'block' : 'none',
    },
    sidebar: {
      position: 'fixed',
      top: '72px',
      left: isOpen ? 0 : '-260px',
      width: '260px',
      height: 'calc(100vh - 72px)',
      backgroundColor: isDarkMode ? '#171717' : '#f7f7f8',
      borderRight: `1px solid ${isDarkMode ? '#2d2d2d' : '#e5e5e5'}`,
      transition: 'left 0.3s ease',
      zIndex: 999,
      display: 'flex',
      flexDirection: 'column',
      fontFamily: 'Inter, sans-serif',
    },
    header: {
      padding: '1rem',
      borderBottom: `1px solid ${isDarkMode ? '#2d2d2d' : '#e5e5e5'}`,
      display: 'flex',
      flexDirection: 'column',
      gap: '0.75rem',
    },
    headerTop: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
    },
    closeButton: {
      background: 'none',
      border: 'none',
      color: isDarkMode ? '#9ca3af' : '#6b7280',
      cursor: 'pointer',
      padding: '0.25rem',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      borderRadius: '4px',
      transition: 'background-color 0.2s ease',
    },
    newChatButton: {
      width: '100%',
      padding: '0.75rem 1rem',
      borderRadius: '8px',
      fontSize: '0.875rem',
      fontWeight: '500',
      cursor: 'pointer',
      display: 'flex',
      alignItems: 'center',
      gap: '0.5rem',
      fontFamily: 'Inter, sans-serif',
      transition: 'all 0.2s ease',
      backgroundColor: isDarkMode ? '#2d2d2d' : '#ffffff',
      color: isDarkMode ? '#ffffff' : '#000000',
      borderWidth: '1px',
      borderStyle: 'solid',
      borderColor: isDarkMode ? '#3d3d3d' : '#e5e5e5',
    },
    newChatButtonHover: {
      backgroundColor: isDarkMode ? '#3d3d3d' : '#f5f5f5',
      borderColor: isDarkMode ? '#4d4d4d' : '#d5d5d5',
    },
    sessionsList: {
      flex: 1,
      overflowY: 'auto',
      padding: '0.5rem',
    },
    sessionItem: {
      padding: '0.75rem 1rem',
      borderRadius: '10px',
      cursor: 'pointer',
      marginBottom: '0.25rem',
      fontSize: '0.875rem',
      fontWeight: '500',
      color: isDarkMode ? '#ececf1' : '#353740',
      transition: 'background-color 0.2s ease, color 0.2s ease, border-color 0.2s ease',
      borderWidth: '1px',
      borderStyle: 'solid',
      borderColor: 'transparent',
      textAlign: 'left',
      position: 'relative',
      display: 'flex',
      alignItems: 'center',
      gap: '0.5rem',
    },
    sessionItemActive: {
      backgroundColor: isDarkMode ? '#2d2d2d' : '#f3f4f6',
      color: isDarkMode ? '#ffffff' : '#111827',
      borderColor: isDarkMode ? '#3d3d3d' : '#e5e7eb',
    },
    sessionItemHover: {
      backgroundColor: isDarkMode ? '#242424' : '#f3f4f6',
      borderColor: isDarkMode ? '#2f2f2f' : '#e5e7eb',
    },
    sessionTitle: {
      display: 'block',
      overflow: 'hidden',
      textOverflow: 'ellipsis',
      whiteSpace: 'nowrap',
      paddingRight: '1.5rem',
    },
    sessionMenuButton: {
      position: 'absolute',
      right: '0.5rem',
      top: '50%',
      transform: 'translateY(-50%)',
      background: 'none',
      border: 'none',
      color: isDarkMode ? '#9ca3af' : '#6b7280',
      cursor: 'pointer',
      padding: '0.25rem',
      borderRadius: '4px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      transition: 'background-color 0.2s ease, opacity 0.2s ease, color 0.2s ease',
      opacity: 0,
      backgroundColor: 'transparent',
    },
    sessionMenuButtonVisible: {
      opacity: 1,
    },
    sessionMenuButtonActive: {
      backgroundColor: isDarkMode ? '#2d2d2d' : '#e5e5e5',
      color: isDarkMode ? '#f3f4f6' : '#111827',
    },
    sessionMenuButtonHover: {
      backgroundColor: isDarkMode ? '#2d2d2d' : '#e5e5e5',
    },
    sessionMenu: {
      position: 'absolute',
      right: '0.5rem',
      top: 'calc(100% + 0.25rem)',
      backgroundColor: isDarkMode ? '#1f1f1f' : '#ffffff',
      borderRadius: '8px',
      boxShadow: isDarkMode ? '0 8px 24px rgba(0,0,0,0.4)' : '0 8px 24px rgba(15,23,42,0.12)',
      border: `1px solid ${isDarkMode ? '#2f2f2f' : '#e5e7eb'}`,
      zIndex: 5,
      minWidth: '140px',
      padding: '0.25rem',
    },
    sessionMenuItem: {
      width: '100%',
      background: 'none',
      border: 'none',
      color: isDarkMode ? '#f87171' : '#b91c1c',
      fontSize: '0.8125rem',
      fontWeight: '500',
      padding: '0.5rem 0.75rem',
      borderRadius: '6px',
      cursor: 'pointer',
      display: 'flex',
      alignItems: 'center',
      gap: '0.5rem',
      transition: 'background-color 0.2s ease, color 0.2s ease',
      backgroundColor: 'transparent',
    },
    sessionMenuItemHover: {
      backgroundColor: isDarkMode ? 'rgba(248,113,113,0.12)' : 'rgba(248,113,113,0.15)',
      color: isDarkMode ? '#fca5a5' : '#991b1b',
    },
    footer: {
      padding: '1rem',
      borderTop: `1px solid ${isDarkMode ? '#2d2d2d' : '#e5e5e5'}`,
      display: 'flex',
      flexDirection: 'column',
      gap: '0.75rem',
    },
    userInfo: {
      display: 'flex',
      alignItems: 'center',
      gap: '0.75rem',
    },
    userAvatar: {
      width: '36px',
      height: '36px',
      borderRadius: '10px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      fontSize: '0.875rem',
      fontWeight: '600',
      backgroundColor: isDarkMode ? '#2d2d2d' : '#ffffff',
      color: isDarkMode ? '#ffffff' : '#000000',
      border: `1px solid ${isDarkMode ? '#3d3d3d' : '#e5e5e5'}`,
    },
    userDetails: {
      display: 'flex',
      flexDirection: 'column',
      gap: '0.25rem',
    },
    userName: {
      fontSize: '0.9375rem',
      fontWeight: '600',
      color: isDarkMode ? '#ececf1' : '#1f2937',
    },
    userEmail: {
      fontSize: '0.8125rem',
      color: isDarkMode ? '#9ca3af' : '#6b7280',
    },
    logoutButton: {
      width: '100%',
      padding: '0.75rem 1rem',
      backgroundColor: isDarkMode ? '#2d2d2d' : '#ffffff',
      color: isDarkMode ? '#ffffff' : '#000000',
      borderWidth: '1px',
      borderStyle: 'solid',
      borderColor: isDarkMode ? '#3d3d3d' : '#e5e5e5',
      borderRadius: '8px',
      fontSize: '0.875rem',
      fontWeight: '500',
      cursor: 'pointer',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      gap: '0.5rem',
      transition: 'all 0.2s ease',
      fontFamily: 'Inter, sans-serif',
    },
    logoutButtonHover: {
      backgroundColor: isDarkMode ? '#3d3d3d' : '#f5f5f5',
      borderColor: isDarkMode ? '#4d4d4d' : '#d5d5d5',
    },
  };

  return (
    <>
      {/* Overlay only for mobile screens - can be clicked to close sidebar */}
      {isOpen && (
        <div 
          style={{
            ...styles.overlay,
            display: window.innerWidth <= 768 ? 'block' : 'none',
          }} 
          onClick={onClose} 
        />
      )}
      <div style={styles.sidebar}>
        <div style={styles.header}>
          <div style={styles.headerTop}>
            <span style={{
              fontSize: '0.875rem',
              fontWeight: '600',
              color: isDarkMode ? '#ececf1' : '#353740',
            }}>
              Sessions
            </span>
            <button
              style={styles.closeButton}
              onClick={onClose}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = isDarkMode ? '#2d2d2d' : '#e5e5e5';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = 'transparent';
              }}
              aria-label="Close sidebar"
            >
              <svg width="20" height="20" viewBox="0 0 16 16" fill="none">
                <path d="M12 4L4 12M4 4l8 8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
              </svg>
            </button>
          </div>
          <button
            style={{
              ...styles.newChatButton,
              ...(isNewChatHovered ? styles.newChatButtonHover : {}),
            }}
            onClick={() => {
              setOpenMenuSessionId(null);
              onNewChat();
            }}
            onMouseEnter={() => setIsNewChatHovered(true)}
            onMouseLeave={() => setIsNewChatHovered(false)}
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M8 2a1 1 0 0 0-1 1v4H3a1 1 0 1 0 0 2h4v4a1 1 0 1 0 2 0V9h4a1 1 0 1 0 0-2H9V3a1 1 0 0 0-1-1Z" fill="currentColor"/>
            </svg>
            New Interview
          </button>
        </div>
        <div style={styles.sessionsList}>
          {chatSessions.map((session) => {
            const isActive = session.id === currentSessionId;
            const isHovered = hoveredSessionId === session.id;
            const isMenuOpen = openMenuSessionId === session.id;

            return (
            <div
              key={session.id}
              style={{
                ...styles.sessionItem,
                  ...(isActive ? styles.sessionItemActive : {}),
                  ...(!isActive && isHovered ? styles.sessionItemHover : {}),
              }}
                onClick={() => {
                  setOpenMenuSessionId(null);
                  onSelectSession(session.id);
                }}
                onMouseEnter={() => setHoveredSessionId(session.id)}
                onMouseLeave={() => setHoveredSessionId(null)}
                role="button"
                tabIndex={0}
                onKeyPress={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    setOpenMenuSessionId(null);
                    onSelectSession(session.id);
                  }
                }}
              >
                <span style={styles.sessionTitle}>{session.title}</span>
                <button
                  type="button"
                  style={{
                    ...styles.sessionMenuButton,
                    ...((isHovered || isMenuOpen) ? styles.sessionMenuButtonVisible : {}),
                    ...((isMenuOpen || hoveredMenuButtonId === session.id) ? styles.sessionMenuButtonActive : {}),
                  }}
                  aria-label="Open chat menu"
                  onClick={(e) => {
                    e.stopPropagation();
                    setOpenMenuSessionId(isMenuOpen ? null : session.id);
              }}
                  onMouseEnter={() => setHoveredMenuButtonId(session.id)}
                  onMouseLeave={() => setHoveredMenuButtonId(null)}
                >
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                    <path d="M8 3a1.25 1.25 0 1 1 0 2.5A1.25 1.25 0 0 1 8 3Zm0 3.75a1.25 1.25 0 1 1 0 2.5 1.25 1.25 0 0 1 0-2.5Zm0 3.75a1.25 1.25 0 1 1 0 2.5 1.25 1.25 0 0 1 0-2.5Z" fill="currentColor"/>
                  </svg>
                </button>
                {isMenuOpen && (
                  <div
                    style={styles.sessionMenu}
                    role="menu"
                  >
                    <button
                      type="button"
                      style={{
                        ...styles.sessionMenuItem,
                        ...(hoveredMenuItemId === session.id ? styles.sessionMenuItemHover : {}),
                      }}
                      onClick={(e) => {
                        e.stopPropagation();
                        setOpenMenuSessionId(null);
                        setHoveredMenuItemId(null);
                        onDeleteSession(session.id);
                      }}
                      onMouseEnter={() => setHoveredMenuItemId(session.id)}
                      onMouseLeave={() => setHoveredMenuItemId(null)}
                    >
                      <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
                        <path d="M6.5 2a1 1 0 0 0-.894.553L5.382 3H3.5a.5.5 0 0 0 0 1h.528l.89 8.012A1.5 1.5 0 0 0 6.408 13.5h3.184a1.5 1.5 0 0 0 1.49-1.488L11.973 4H12.5a.5.5 0 0 0 0-1h-1.882l-.224-.447A1 1 0 0 0 9.5 2h-3Zm-.235 2 .813 7.312a.5.5 0 0 0 .497.438h1.85a.5.5 0 0 0 .497-.438L10.235 4H6.265Z" fill="currentColor"/>
                      </svg>
                      Delete chat
                    </button>
                  </div>
                )}
              </div>
          );
          })}
        </div>
        {user && (
          <div style={styles.footer}>
            <div style={styles.userInfo}>
              <div style={styles.userAvatar}>{getUserInitials()}</div>
              <div style={styles.userDetails}>
                <span style={styles.userName}>{user.name || user.email}</span>
                {user.name && user.email && (
                  <span style={styles.userEmail}>{user.email}</span>
                )}
              </div>
            </div>
            <button
              style={{
                ...styles.logoutButton,
                ...(isLogoutHovered ? styles.logoutButtonHover : {}),
              }}
              onClick={() => {
                setOpenMenuSessionId(null);
                onLogout();
              }}
              onMouseEnter={() => setIsLogoutHovered(true)}
              onMouseLeave={() => setIsLogoutHovered(false)}
            >
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <path d="M6 2a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V9h2v4h4V3H8v4H6V2Z" fill="currentColor"/>
                <path d="M3.707 5.293a1 1 0 0 0-1.414 1.414L3.586 8l-1.293 1.293a1 1 0 1 0 1.414 1.414L6.414 8 3.707 5.293Z" fill="currentColor"/>
              </svg>
              Logout
            </button>
            </div>
        )}
      </div>
    </>
  );
}

export default Sidebar;


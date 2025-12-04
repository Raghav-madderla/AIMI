import React, { useState, useEffect } from 'react';
import './App.css';
import SetupScreen from './SetupScreen';
import ChatInterviewScreen from './ChatInterviewScreen';
import Sidebar from './Sidebar';
import LoginScreen from './LoginScreen';
import { apiService } from './api';

const NAVBAR_HEIGHT = 72;

function App() {
  // Authentication state
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [checkingAuth, setCheckingAuth] = useState(true);

  // 'setup' or 'interview'
  const [appState, setAppState] = useState('interview');

  // Chat sessions management
  const [chatSessions, setChatSessions] = useState([]);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [currentQuestion, setCurrentQuestion] = useState(null);
  const [backendConnected, setBackendConnected] = useState(false);
  
  // Dark mode state (default: dark mode)
  const [isDarkMode, setIsDarkMode] = useState(true);
  const [showSetupModal, setShowSetupModal] = useState(false);

  // Check authentication on mount
  useEffect(() => {
    const checkAuth = () => {
      const token = apiService.getAuthToken();
      const storedUser = localStorage.getItem('user');
      
      if (token && storedUser) {
        try {
          setUser(JSON.parse(storedUser));
          setIsAuthenticated(true);
        } catch (error) {
          console.error('Error parsing user data:', error);
          localStorage.removeItem('authToken');
          localStorage.removeItem('user');
        }
      }
      setCheckingAuth(false);
    };

    checkAuth();
  }, []);

  // Check backend connection and load sessions when authenticated
  useEffect(() => {
    if (isAuthenticated) {
      const checkBackend = async () => {
        try {
          await apiService.healthCheck();
          setBackendConnected(true);
          // Load existing sessions
          loadSessions();
        } catch (error) {
          setBackendConnected(false);
          setError('Cannot connect to backend. Please ensure the backend server is running on http://localhost:8000');
        }
      };
      checkBackend();
    }
  }, [isAuthenticated]);

  const loadSessions = async () => {
    try {
      const result = await apiService.getAllSessions();
      // Backend returns { sessions: [...] }
      const sessions = result.sessions || [];
      const formattedSessions = sessions.map(session => ({
        id: session.id || session.session_id,
        title: session.title || `Interview - ${session.job_role}`,
        messages: [],
        createdAt: session.createdAt || session.created_at,
        resumeId: session.resume_id,
        jobRole: session.job_role,
      }));
      setChatSessions(formattedSessions);
    } catch (error) {
      console.error('Failed to load sessions:', error);
      setChatSessions([]); // Set empty array on error
    }
  };

  const loadSessionMessages = async (sessionId) => {
    try {
      const result = await apiService.getSessionMessages(sessionId);
      return result.messages.map(msg => {
        // All messages are displayed as-is (no detailed report formatting)
        return {
          role: msg.role,
          content: msg.content,
          questionData: msg.metadata || msg.message_metadata || null,
          feedback: (msg.metadata || msg.message_metadata)?.feedback || null,
        };
      });
    } catch (error) {
      console.error('Failed to load messages:', error);
      return [];
    }
  };

  // Get current session messages
  const getCurrentSession = () => {
    return chatSessions.find(s => s.id === currentSessionId);
  };

  const getCurrentMessages = () => {
    const session = getCurrentSession();
    return session ? session.messages : [];
  };

  // Fetch messages from backend for a session
  const fetchSessionData = async (sessionId) => {
    try {
      const messages = await loadSessionMessages(sessionId);
      const session = chatSessions.find(s => s.id === sessionId);
      if (session) {
        updateSession(sessionId, { messages });
        // Set current question from last assistant message
        const lastQuestion = messages.filter(m => m.role === 'assistant' && m.questionData).pop();
        if (lastQuestion) {
          setCurrentQuestion(lastQuestion.questionData);
        }
      }
    } catch (error) {
      console.error('Failed to fetch session data:', error);
    }
  };

  // Update a session
  const updateSession = (sessionId, updates) => {
    setChatSessions(sessions =>
      sessions.map(s => s.id === sessionId ? { ...s, ...updates } : s)
    );
  };

  // Handle starting a new interview
  const handleStartInterview = async (resumeId, jobRole) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const result = await apiService.startInterview(resumeId, jobRole);
      const sessionId = result.session_id;
      const message = result.message || result.message_text; // Welcome message
      const question = result.question; // May be undefined for welcome phase
      
      // Create session object
      const newSession = {
        id: sessionId,
        title: `Interview - ${jobRole}`,
        messages: [{
          role: 'assistant',
          content: message || (question ? question.question_text : ''),
          questionData: question || { type: 'welcome', round: 'welcome' },
        }],
        createdAt: new Date().toISOString(),
        resumeId: resumeId,
        jobRole: jobRole,
      };
      
      // Add to sessions list
      setChatSessions(sessions => [newSession, ...sessions]);
      setCurrentSessionId(sessionId);
      setCurrentQuestion(question || null); // Set to null for welcome phase
      setAppState('interview');
      setSidebarOpen(true);
      setShowSetupModal(false);
    } catch (error) {
      const normalizedError = error instanceof Error ? error : new Error(error?.message || 'Failed to start interview');
      setError(normalizedError.message || 'Failed to start interview');
      console.error('Start interview error:', normalizedError);
      throw normalizedError;
    } finally {
      setIsLoading(false);
    }
  };

  // Handle sending a message (answer)
  const handleSendMessage = async (answerText) => {
    if (!currentSessionId) return;

    // Add user message to UI immediately using functional update
    const userMessage = {
      role: 'user',
      content: answerText,
    };
    
    // Use functional update to ensure we have latest state
    setChatSessions(prevSessions => 
      prevSessions.map(s => 
        s.id === currentSessionId 
          ? { ...s, messages: [...(s.messages || []), userMessage] }
          : s
      )
    );

    setIsLoading(true);
    setError(null);

    try {
      // Submit answer to backend
      // For welcome phase, question/domain/difficulty are optional
      const result = await apiService.submitAnswer(
        currentSessionId,
        answerText,
        currentQuestion?.question_text || '',
        currentQuestion?.domain || currentQuestion?.skill || '',
        currentQuestion?.difficulty || ''
      );

      // Handle welcome phase response (no evaluation)
      if (result.message && !result.evaluation) {
        // Add assistant response message
        setChatSessions(prevSessions => 
          prevSessions.map(s => 
            s.id === currentSessionId 
              ? { 
                  ...s, 
                  messages: [
                    ...s.messages,
                    {
                      role: 'assistant',
                      content: result.message,
                      questionData: { type: 'response', round: 'welcome' },
                    }
                  ]
                }
              : s
          )
        );
        
        // If user confirmed and got first question
        if (result.next_question) {
          const nextQuestion = result.next_question;
          setCurrentQuestion(nextQuestion);
          
          // Add first question as assistant message
          setChatSessions(prevSessions => 
            prevSessions.map(s => 
              s.id === currentSessionId 
                ? { 
                    ...s, 
                    messages: [
                      ...s.messages,
                      {
                        role: 'assistant',
                        content: nextQuestion.question_text,
                        questionData: nextQuestion,
                      }
                    ]
                  }
                : s
            )
          );
        }
        return; // Exit early for welcome phase
      }

      // Regular question evaluation (not welcome phase)
      // Evaluation happens in backend, we just get the next question
      // Don't show evaluation to user - it's used internally by backend
      if (result.evaluation || result.next_question) {
        // Handle next question (evaluation is done in backend, not shown to user)
        if (result.next_question) {
          const nextQuestion = result.next_question;
          setCurrentQuestion(nextQuestion);
          
          // Add next question as assistant message using functional update
          setChatSessions(prevSessions => 
            prevSessions.map(s => 
              s.id === currentSessionId 
                ? { 
                    ...s, 
                    messages: [
                      ...s.messages,
                      {
                        role: 'assistant',
                        content: nextQuestion.question_text,
                        questionData: nextQuestion,
                      }
                    ]
                  }
                : s
            )
          );
        } else {
          // Interview complete - show simple end note
          setCurrentQuestion(null);
          
          // Display completion message (no detailed report)
          const completionMessage = result.message || 'Thank you for completing the interview! Your responses have been recorded. We appreciate your time and effort. Best of luck with your application! 🎉';
            
            setChatSessions(prevSessions => 
              prevSessions.map(s => 
                s.id === currentSessionId 
                  ? { 
                      ...s, 
                      messages: [
                        ...s.messages,
                        {
                          role: 'assistant',
                        content: completionMessage,
                          questionData: { type: 'completion' },
                        }
                      ]
                    }
                  : s
              )
            );
        }
      }
    } catch (error) {
      setError(error.message || 'Failed to submit answer');
      console.error('Submit answer error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle session selection
  const handleSelectSession = async (sessionId) => {
    if (sessionId === currentSessionId) {
      return;
    }
    
    setCurrentSessionId(sessionId);
    setAppState('interview');
    setIsLoading(true);
    
    try {
      // Load session messages from backend
      await fetchSessionData(sessionId);
    } catch (error) {
      setError('Failed to load session messages');
      console.error('Load session error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteSession = async (sessionId) => {
    try {
      await apiService.deleteSession(sessionId);
    } catch (error) {
      console.error('Failed to delete session:', error);
    } finally {
      setChatSessions(prev => prev.filter(session => session.id !== sessionId));
      if (currentSessionId === sessionId) {
        setCurrentSessionId(null);
        setCurrentQuestion(null);
      }
    }
  };

  // Handle new chat - go back to setup screen
  const handleNewChat = () => {
    setAppState('interview');
    setCurrentSessionId(null);
    setCurrentQuestion(null);
    setError(null);
    setShowSetupModal(true);
  };

  // Handle login
  const handleLogin = (userData) => {
    setUser(userData);
    setIsAuthenticated(true);
    setError(null);
  };

  // Handle logout
  const handleLogout = async () => {
    await apiService.logout();
    setIsAuthenticated(false);
    setUser(null);
    setChatSessions([]);
    setCurrentSessionId(null);
    setCurrentQuestion(null);
    setAppState('interview');
    setError(null);
  };

  // Update the render function
  const renderCurrentScreen = () => {
    if (error) {
      return (
        <div style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          height: `calc(100vh - ${NAVBAR_HEIGHT}px)`,
          color: '#dc3545',
          fontFamily: 'Inter, sans-serif',
          fontSize: '0.9375rem',
          fontWeight: '400'
        }}>
          {error}
        </div>
      );
    }

    switch (appState) {
      case 'setup':
        return <SetupScreen onStartInterview={handleStartInterview} isDarkMode={isDarkMode} />;
      case 'interview':
        return (
          <>
            <Sidebar
              chatSessions={chatSessions}
              currentSessionId={currentSessionId}
              onSelectSession={handleSelectSession}
              onNewChat={handleNewChat}
              isDarkMode={isDarkMode}
              isOpen={sidebarOpen}
              onClose={() => setSidebarOpen(false)}
              user={user}
              onLogout={handleLogout}
              onDeleteSession={handleDeleteSession}
            />
            <div style={{ marginLeft: sidebarOpen ? '260px' : '0', transition: 'margin-left 0.3s ease' }}>
              {currentSessionId ? (
                <ChatInterviewScreen
                  messages={getCurrentMessages()}
                  onSendMessage={handleSendMessage}
                  isLoading={isLoading}
                  isDarkMode={isDarkMode}
                  currentQuestion={currentQuestion}
                  user={user}
                />
              ) : (
                <div style={{
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'center',
                  alignItems: 'center',
                  height: `calc(100vh - ${NAVBAR_HEIGHT}px)`,
                  padding: '2rem',
                  textAlign: 'center',
                  fontFamily: 'Inter, sans-serif',
                  backgroundColor: isDarkMode ? '#0f0f0f' : '#ffffff',
                  color: isDarkMode ? '#ececf1' : '#353740',
                }}>
                  <div style={{
                    fontSize: '2.5rem',
                    fontWeight: '600',
                    marginBottom: '1rem',
                    color: isDarkMode ? '#ffffff' : '#000000',
                  }}>
                    Welcome to AIMI
                  </div>
                  <p style={{
                    fontSize: '1rem',
                    color: isDarkMode ? '#9ca3af' : '#6b7280',
                    maxWidth: '600px',
                    marginBottom: '2rem',
                    lineHeight: '1.6',
                  }}>
                    Your AI-powered interview assistant. Click "New Interview" in the sidebar to get started with your personalized interview experience.
                  </p>
                  <button
                    onClick={handleNewChat}
                    style={{
                      padding: '0.875rem 2rem',
                      backgroundColor: isDarkMode ? '#2d2d2d' : '#ffffff',
                      color: isDarkMode ? '#ffffff' : '#000000',
                      border: `1px solid ${isDarkMode ? '#3d3d3d' : '#e5e5e5'}`,
                      borderRadius: '8px',
                      fontSize: '1rem',
                      fontWeight: '500',
                      cursor: 'pointer',
                      fontFamily: 'Inter, sans-serif',
                      transition: 'all 0.2s ease',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.5rem',
                    }}
                    onMouseEnter={(e) => {
                      e.target.style.backgroundColor = isDarkMode ? '#3d3d3d' : '#f5f5f5';
                      e.target.style.borderColor = isDarkMode ? '#4d4d4d' : '#d5d5d5';
                    }}
                    onMouseLeave={(e) => {
                      e.target.style.backgroundColor = isDarkMode ? '#2d2d2d' : '#ffffff';
                      e.target.style.borderColor = isDarkMode ? '#3d3d3d' : '#e5e5e5';
                    }}
                  >
                    <svg width="20" height="20" viewBox="0 0 16 16" fill="none">
                      <path d="M8 2a1 1 0 0 0-1 1v4H3a1 1 0 1 0 0 2h4v4a1 1 0 1 0 2 0V9h4a1 1 0 1 0 0-2H9V3a1 1 0 0 0-1-1Z" fill="currentColor"/>
                    </svg>
                    Start New Interview
                  </button>
                </div>
              )}
            </div>
            {!sidebarOpen && (
              <button
                onClick={() => setSidebarOpen(true)}
                style={{
                  position: 'fixed',
                  left: '0',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  padding: '0.5rem',
                  backgroundColor: isDarkMode ? '#2d2d2d' : '#e5e5e5',
                  border: 'none',
                  borderTopRightRadius: '8px',
                  borderBottomRightRadius: '8px',
                  cursor: 'pointer',
                  zIndex: 1000,
                }}
              >
                <svg width="20" height="20" viewBox="0 0 16 16" fill="none">
                  <path d="M2 4h12M2 8h12M2 12h12" stroke={isDarkMode ? '#ececf1' : '#353740'} strokeWidth="1.5"/>
                </svg>
              </button>
            )}
          </>
        );
      default:
        return <SetupScreen onStartInterview={handleStartInterview} isDarkMode={isDarkMode} />;
    }
  };

  const toggleDarkMode = () => {
    setIsDarkMode(!isDarkMode);
  };

  const handleCloseSetupModal = () => {
    setShowSetupModal(false);
  };

  useEffect(() => {
    if (showSetupModal) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }

    return () => {
      document.body.style.overflow = '';
    };
  }, [showSetupModal]);

  // Show loading screen while checking authentication
  if (checkingAuth) {
    return (
      <div className={`App ${isDarkMode ? 'dark-mode' : ''}`} style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        fontFamily: 'Inter, sans-serif',
        color: isDarkMode ? '#e0e0e0' : '#333',
      }}>
        <div>Loading...</div>
      </div>
    );
  }

  // Show login screen if not authenticated
  if (!isAuthenticated) {
    return (
      <div className={`App ${isDarkMode ? 'dark-mode' : ''}`}>
        <nav className="navbar">
          <div className="logo">
            <span className="logo-text">AIMI</span>
          </div>
          <div className="header-actions">
            <button 
              className={`theme-toggle ${isDarkMode ? 'dark' : 'light'}`}
              onClick={toggleDarkMode}
              aria-label="Toggle dark mode"
            >
              {isDarkMode ? '☀️' : '🌙'}
            </button>
          </div>
        </nav>
        <header className="App-header">
          <LoginScreen onLogin={handleLogin} isDarkMode={isDarkMode} />
        </header>
      </div>
    );
  }

  return (
    <div className={`App ${isDarkMode ? 'dark-mode' : ''}`}>
      <nav className="navbar">
        <div className="logo">
          <span className="logo-text">AIMI</span>
        </div>
        <div className="header-actions">
          <button 
            className={`theme-toggle ${isDarkMode ? 'dark' : 'light'}`}
            onClick={toggleDarkMode}
            aria-label="Toggle dark mode"
            style={{ marginRight: '0.5rem' }}
          >
            {isDarkMode ? '☀️' : '🌙'}
          </button>
        </div>
      </nav>
      {showSetupModal && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: isDarkMode ? 'rgba(12,12,12,0.65)' : 'rgba(15,23,42,0.45)',
            backdropFilter: 'blur(8px)',
            WebkitBackdropFilter: 'blur(8px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '2rem',
            zIndex: 1200,
          }}
          onClick={handleCloseSetupModal}
          role="presentation"
        >
          <div
            style={{
              width: '100%',
              maxWidth: '520px',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <SetupScreen
              onStartInterview={handleStartInterview}
              isDarkMode={isDarkMode}
              onClose={handleCloseSetupModal}
              isModal
            />
          </div>
        </div>
      )}
      <div style={{ 
        position: 'relative',
        minHeight: `calc(100vh - ${NAVBAR_HEIGHT}px)`,
      }}>
        {appState === 'interview' ? (
          renderCurrentScreen()
        ) : (
          <header className="App-header">
            <SetupScreen onStartInterview={handleStartInterview} isDarkMode={isDarkMode} />
          </header>
        )}
      </div>
    </div>
  );
}

export default App;


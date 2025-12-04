import React, { useState } from 'react';
import { apiService } from './api';

function LoginScreen({ onLogin, isDarkMode }) {
  const [isLogin, setIsLogin] = useState(true); // true for login, false for register
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [name, setName] = useState(''); // For registration
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const styles = {
    container: {
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      padding: '2.5rem',
      backgroundColor: isDarkMode ? '#1e1e1e' : '#fff',
      borderRadius: '12px',
      boxShadow: isDarkMode ? '0 4px 12px rgba(0, 0, 0, 0.5)' : '0 4px 12px rgba(0, 0, 0, 0.1)',
      width: '450px',
      margin: '2rem auto',
      transition: 'background-color 0.3s ease, box-shadow 0.3s ease',
    },
    title: {
      color: isDarkMode ? '#e0e0e0' : '#333',
      marginBottom: '0.5rem',
      fontSize: '1.75rem',
      fontWeight: '700',
      letterSpacing: '-0.02em',
      fontFamily: 'Inter, sans-serif',
    },
    subtitle: {
      color: isDarkMode ? '#9ca3af' : '#6b7280',
      marginBottom: '2rem',
      fontSize: '0.9375rem',
      fontWeight: '400',
      fontFamily: 'Inter, sans-serif',
    },
    formGroup: {
      width: '100%',
      marginBottom: '1.25rem',
    },
    label: {
      display: 'block',
      marginBottom: '0.625rem',
      color: isDarkMode ? '#e0e0e0' : '#1f2937',
      textAlign: 'left',
      fontSize: '0.9375rem',
      fontWeight: '500',
      letterSpacing: '-0.01em',
      fontFamily: 'Inter, sans-serif',
    },
    input: {
      width: '100%',
      padding: '0.875rem 1rem',
      fontSize: '0.9375rem',
      fontWeight: '400',
      borderRadius: '8px',
      border: `1px solid ${isDarkMode ? '#444' : '#d1d5db'}`,
      backgroundColor: isDarkMode ? '#2a2a2a' : '#fff',
      color: isDarkMode ? '#e0e0e0' : '#1f2937',
      transition: 'background-color 0.3s ease, border-color 0.3s ease, color 0.3s ease',
      fontFamily: 'Inter, sans-serif',
      outline: 'none',
    },
    inputFocus: {
      borderColor: isDarkMode ? '#5d5d5d' : '#9ca3af',
      boxShadow: isDarkMode ? '0 0 0 3px rgba(93, 93, 93, 0.1)' : '0 0 0 3px rgba(156, 163, 175, 0.1)',
    },
    submitButton: {
      width: '100%',
      padding: '0.875rem 1.5rem',
      fontSize: '0.9375rem',
      fontWeight: '600',
      color: isDarkMode ? '#ffffff' : '#000000',
      backgroundColor: isDarkMode ? '#2d2d2d' : '#ffffff',
      border: `1px solid ${isDarkMode ? '#3d3d3d' : '#e5e5e5'}`,
      borderRadius: '8px',
      cursor: isLoading ? 'not-allowed' : 'pointer',
      transition: 'all 0.3s ease',
      fontFamily: 'Inter, sans-serif',
      letterSpacing: '-0.01em',
      marginTop: '0.5rem',
      opacity: isLoading ? 0.6 : 1,
    },
    toggleButton: {
      width: '100%',
      padding: '0.75rem 1.5rem',
      fontSize: '0.875rem',
      fontWeight: '400',
      color: isDarkMode ? '#9ca3af' : '#6b7280',
      backgroundColor: 'transparent',
      border: 'none',
      cursor: 'pointer',
      marginTop: '1rem',
      fontFamily: 'Inter, sans-serif',
      textDecoration: 'underline',
    },
    errorMessage: {
      color: '#dc3545',
      fontSize: '0.875rem',
      marginBottom: '1rem',
      textAlign: 'center',
      fontFamily: 'Inter, sans-serif',
      padding: '0.75rem',
      backgroundColor: isDarkMode ? '#2a1a1a' : '#ffe6e6',
      borderRadius: '8px',
      border: `1px solid ${isDarkMode ? '#5a2a2a' : '#ffcccc'}`,
    },
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      if (isLogin) {
        // Login
        if (!email || !password) {
          setError('Please fill in all fields');
          setIsLoading(false);
          return;
        }
        const result = await apiService.login(email, password);
        if (result.token) {
          localStorage.setItem('authToken', result.token);
          localStorage.setItem('user', JSON.stringify(result.user || { email }));
          onLogin(result.user || { email });
        }
      } else {
        // Register
        if (!email || !password || !name) {
          setError('Please fill in all fields');
          setIsLoading(false);
          return;
        }
        if (password !== confirmPassword) {
          setError('Passwords do not match');
          setIsLoading(false);
          return;
        }
        if (password.length < 6) {
          setError('Password must be at least 6 characters');
          setIsLoading(false);
          return;
        }
        const result = await apiService.register(email, password, name);
        if (result.token) {
          localStorage.setItem('authToken', result.token);
          localStorage.setItem('user', JSON.stringify(result.user || { email, name }));
          onLogin(result.user || { email, name });
        }
      }
    } catch (error) {
      setError(error.message || (isLogin ? 'Login failed' : 'Registration failed'));
      setIsLoading(false);
    }
  };

  const toggleMode = () => {
    setIsLogin(!isLogin);
    setError(null);
    setPassword('');
    setConfirmPassword('');
  };

  return (
    <div style={styles.container}>
      <h1 style={styles.title}>{isLogin ? 'Welcome Back' : 'Create Account'}</h1>
      <p style={styles.subtitle}>
        {isLogin ? 'Sign in to continue to AIMI' : 'Sign up to get started with AIMI'}
      </p>

      {error && <div style={styles.errorMessage}>{error}</div>}

      <form onSubmit={handleSubmit} style={{ width: '100%' }}>
        {!isLogin && (
          <div style={styles.formGroup}>
            <label style={styles.label}>Full Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Enter your name"
              disabled={isLoading}
              style={styles.input}
              onFocus={(e) => {
                e.target.style.borderColor = isDarkMode ? '#5d5d5d' : '#9ca3af';
                e.target.style.boxShadow = isDarkMode 
                  ? '0 0 0 3px rgba(93, 93, 93, 0.1)' 
                  : '0 0 0 3px rgba(156, 163, 175, 0.1)';
              }}
              onBlur={(e) => {
                e.target.style.borderColor = isDarkMode ? '#444' : '#d1d5db';
                e.target.style.boxShadow = 'none';
              }}
            />
          </div>
        )}

        <div style={styles.formGroup}>
          <label style={styles.label}>Email</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Enter your email"
            disabled={isLoading}
            style={styles.input}
            onFocus={(e) => {
              e.target.style.borderColor = isDarkMode ? '#19c37d' : '#10a37f';
              e.target.style.boxShadow = isDarkMode 
                ? '0 0 0 3px rgba(25, 195, 125, 0.1)' 
                : '0 0 0 3px rgba(16, 163, 127, 0.1)';
            }}
            onBlur={(e) => {
              e.target.style.borderColor = isDarkMode ? '#444' : '#d1d5db';
              e.target.style.boxShadow = 'none';
            }}
          />
        </div>

        <div style={styles.formGroup}>
          <label style={styles.label}>Password</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Enter your password"
            disabled={isLoading}
            style={styles.input}
            onFocus={(e) => {
              e.target.style.borderColor = isDarkMode ? '#19c37d' : '#10a37f';
              e.target.style.boxShadow = isDarkMode 
                ? '0 0 0 3px rgba(25, 195, 125, 0.1)' 
                : '0 0 0 3px rgba(16, 163, 127, 0.1)';
            }}
            onBlur={(e) => {
              e.target.style.borderColor = isDarkMode ? '#444' : '#d1d5db';
              e.target.style.boxShadow = 'none';
            }}
          />
        </div>

        {!isLogin && (
          <div style={styles.formGroup}>
            <label style={styles.label}>Confirm Password</label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Confirm your password"
              disabled={isLoading}
              style={styles.input}
              onFocus={(e) => {
                e.target.style.borderColor = isDarkMode ? '#5d5d5d' : '#9ca3af';
                e.target.style.boxShadow = isDarkMode 
                  ? '0 0 0 3px rgba(93, 93, 93, 0.1)' 
                  : '0 0 0 3px rgba(156, 163, 175, 0.1)';
              }}
              onBlur={(e) => {
                e.target.style.borderColor = isDarkMode ? '#444' : '#d1d5db';
                e.target.style.boxShadow = 'none';
              }}
            />
          </div>
        )}

        <button
          type="submit"
          style={styles.submitButton}
          disabled={isLoading}
          onMouseEnter={(e) => {
            if (!isLoading) {
              e.target.style.backgroundColor = isDarkMode ? '#3d3d3d' : '#f5f5f5';
              e.target.style.borderColor = isDarkMode ? '#4d4d4d' : '#d5d5d5';
            }
          }}
          onMouseLeave={(e) => {
            e.target.style.backgroundColor = isDarkMode ? '#2d2d2d' : '#ffffff';
            e.target.style.borderColor = isDarkMode ? '#3d3d3d' : '#e5e5e5';
          }}
        >
          {isLoading ? (isLogin ? 'Signing in...' : 'Creating account...') : (isLogin ? 'Sign In' : 'Sign Up')}
        </button>
      </form>

      <button
        type="button"
        style={styles.toggleButton}
        onClick={toggleMode}
        disabled={isLoading}
      >
        {isLogin 
          ? "Don't have an account? Sign up" 
          : 'Already have an account? Sign in'}
      </button>
    </div>
  );
}

export default LoginScreen;


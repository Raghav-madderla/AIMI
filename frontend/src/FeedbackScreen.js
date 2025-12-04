import React from 'react';

function FeedbackScreen({ feedbackData, onNextQuestion, onEndInterview, isDarkMode }) {
  if (!feedbackData) {
    return <div style={{ color: isDarkMode ? '#e0e0e0' : '#333' }}>Loading feedback...</div>;
  }

  const { overall_score, feedback_text } = feedbackData;
  const scorePercentage = (overall_score * 100).toFixed(0);

  // Dynamic styles based on dark mode
  const styles = {
    container: {
      padding: '2.5rem',
      backgroundColor: isDarkMode ? '#1e1e1e' : '#fff',
      borderRadius: '12px',
      boxShadow: isDarkMode ? '0 4px 12px rgba(0, 0, 0, 0.5)' : '0 4px 12px rgba(0, 0, 0, 0.1)',
      width: '450px',
      margin: '2rem auto',
      color: isDarkMode ? '#e0e0e0' : '#1f2937',
      transition: 'background-color 0.3s ease, box-shadow 0.3s ease, color 0.3s ease',
      fontFamily: 'Inter, sans-serif',
    },
    title: {
      textAlign: 'center',
      marginBottom: '1.5rem',
      color: isDarkMode ? '#e0e0e0' : '#1f2937',
      fontSize: '1.25rem',
      fontWeight: '600',
      letterSpacing: '-0.02em',
      fontFamily: 'Inter, sans-serif',
    },
    scoreCircle: {
      width: '160px',
      height: '160px',
      borderRadius: '50%',
      backgroundColor: isDarkMode ? '#2a2a2a' : '#f9fafb',
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'center',
      alignItems: 'center',
      margin: '0 auto 1.5rem auto',
      border: '8px solid #28a745',
      transition: 'background-color 0.3s ease',
    },
    scoreText: {
      fontSize: '0.875rem',
      fontWeight: '500',
      color: isDarkMode ? '#9ca3af' : '#6b7280',
      margin: 0,
      letterSpacing: '0.025em',
      fontFamily: 'Inter, sans-serif',
    },
    score: {
      fontSize: '2.75rem',
      fontWeight: '700',
      color: isDarkMode ? '#e0e0e0' : '#1f2937',
      margin: '0.25rem 0 0 0',
      letterSpacing: '-0.02em',
      fontFamily: 'Inter, sans-serif',
    },
    feedbackText: {
      fontSize: '0.9375rem',
      lineHeight: '1.75',
      textAlign: 'center',
      marginBottom: '1.5rem',
      color: isDarkMode ? '#d1d5db' : '#4b5563',
      fontWeight: '400',
      letterSpacing: '-0.01em',
      fontFamily: 'Inter, sans-serif',
    },
    buttonContainer: {
      display: 'flex',
      gap: '1rem',
    },
    nextButton: {
      flex: 1,
      padding: '0.875rem 1.5rem',
      fontSize: '0.9375rem',
      fontWeight: '600',
      color: '#fff',
      backgroundColor: '#007bff',
      border: 'none',
      borderRadius: '8px',
      cursor: 'pointer',
      transition: 'background-color 0.3s ease',
      fontFamily: 'Inter, sans-serif',
      letterSpacing: '-0.01em',
    },
    endButton: {
      flex: 1,
      padding: '0.875rem 1.5rem',
      fontSize: '0.9375rem',
      fontWeight: '600',
      color: '#fff',
      backgroundColor: '#dc3545',
      border: 'none',
      borderRadius: '8px',
      cursor: 'pointer',
      transition: 'background-color 0.3s ease',
      fontFamily: 'Inter, sans-serif',
      letterSpacing: '-0.01em',
    },
  };

  return (
    <div style={styles.container}>
      <h2 style={styles.title}>Your Performance Report</h2>

      <div style={styles.scoreCircle}>
        <span style={styles.scoreText}>Overall Score</span>
        <span style={styles.score}>{scorePercentage}%</span>
      </div>

      <p style={styles.feedbackText}>{feedback_text}</p>

      {/* 2. Add a button container */}
      <div style={styles.buttonContainer}>
        <button
          style={styles.nextButton}
          onClick={onNextQuestion}
          onMouseEnter={(e) => e.target.style.backgroundColor = '#0056b3'}
          onMouseLeave={(e) => e.target.style.backgroundColor = '#007bff'}
        >
          Next Question
        </button>
        <button
          style={styles.endButton}
          onClick={onEndInterview}
          onMouseEnter={(e) => e.target.style.backgroundColor = '#c82333'}
          onMouseLeave={(e) => e.target.style.backgroundColor = '#dc3545'}
        >
          End Interview
        </button>
      </div>
    </div>
  );
}

export default FeedbackScreen;


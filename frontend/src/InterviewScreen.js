import React, { useState } from 'react';

function InterviewScreen({ questionData, onSubmitAnswer, isDarkMode }) {
  // 2. State to hold the user's answer
  const [answer, setAnswer] = useState('');

  if (!questionData) {
    return <div style={{ color: isDarkMode ? '#e0e0e0' : '#333' }}>Loading question...</div>;
  }

  const { skill, difficulty, question_text } = questionData;

  // 3. This function will be called when the button is clicked
  const handleSubmit = () => {
    onSubmitAnswer(answer);
  };

  // Dynamic styles based on dark mode
  const styles = {
    container: {
      padding: '2.5rem',
      backgroundColor: isDarkMode ? '#1e1e1e' : '#fff',
      borderRadius: '12px',
      boxShadow: isDarkMode ? '0 4px 12px rgba(0, 0, 0, 0.5)' : '0 4px 12px rgba(0, 0, 0, 0.1)',
      width: '650px',
      margin: '2rem auto',
      color: isDarkMode ? '#e0e0e0' : '#1f2937',
      transition: 'background-color 0.3s ease, box-shadow 0.3s ease, color 0.3s ease',
      fontFamily: 'Inter, sans-serif',
    },
    header: {
      marginBottom: '1.5rem',
      borderBottom: `1px solid ${isDarkMode ? '#444' : '#e5e7eb'}`,
      paddingBottom: '1rem',
    },
    skill: {
      fontSize: '0.875rem',
      fontWeight: '600',
      color: isDarkMode ? '#9ca3af' : '#6b7280',
      textTransform: 'uppercase',
      letterSpacing: '0.05em',
      fontFamily: 'Inter, sans-serif',
    },
    question: {
      fontSize: '1.125rem',
      lineHeight: '1.75',
      marginBottom: '2rem',
      color: isDarkMode ? '#e0e0e0' : '#1f2937',
      fontWeight: '400',
      letterSpacing: '-0.01em',
      fontFamily: 'Inter, sans-serif',
    },
    answerArea: {
      width: '100%',
      minHeight: '180px',
      fontSize: '0.9375rem',
      fontWeight: '400',
      padding: '1rem',
      border: `1px solid ${isDarkMode ? '#444' : '#d1d5db'}`,
      borderRadius: '8px',
      backgroundColor: isDarkMode ? '#2a2a2a' : '#fff',
      color: isDarkMode ? '#e0e0e0' : '#1f2937',
      transition: 'background-color 0.3s ease, border-color 0.3s ease, color 0.3s ease',
      fontFamily: 'Inter, sans-serif',
      lineHeight: '1.6',
      resize: 'vertical',
    },
    submitButton: {
      width: '100%',
      padding: '0.875rem 1.5rem',
      fontSize: '0.9375rem',
      fontWeight: '600',
      color: '#fff',
      backgroundColor: '#28a745',
      border: 'none',
      borderRadius: '8px',
      cursor: 'pointer',
      marginTop: '1rem',
      transition: 'background-color 0.3s ease',
      fontFamily: 'Inter, sans-serif',
      letterSpacing: '-0.01em',
    },
  };

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <span style={styles.skill}>{skill} ({difficulty})</span>
      </div>
      <p style={styles.question}>{question_text}</p>

      <textarea
        style={styles.answerArea}
        placeholder="Type your answer here..."
        value={answer} // 4. Bind value to state
        onChange={(e) => setAnswer(e.target.value)} // 5. Update state on change
      />
      <button
        style={styles.submitButton}
        onClick={handleSubmit}
        onMouseEnter={(e) => e.target.style.backgroundColor = '#218838'}
        onMouseLeave={(e) => e.target.style.backgroundColor = '#28a745'}
      >
        Submit Answer
      </button>
    </div>
  );
}

export default InterviewScreen;


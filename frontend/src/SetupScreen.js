import React, { useState, useRef } from 'react';
import { apiService } from './api';

function SetupScreen({ onStartInterview, isDarkMode, onClose, isModal = false }) {
  // State to hold the selected values
  const [jobRole, setJobRole] = useState('Data Scientist');
  const [selectedFile, setSelectedFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);
  const fileInputRef = useRef(null);
  const [resumeId, setResumeId] = useState(null);
  const [isStartHovered, setIsStartHovered] = useState(false);
  const [isCloseHovered, setIsCloseHovered] = useState(false);

  // Dynamic styles based on dark mode
  const styles = {
    container: {
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      padding: '2.5rem',
      backgroundColor: isDarkMode ? '#1e1e1e' : '#fff',
      borderRadius: '12px',
      boxShadow: isDarkMode ? '0 4px 12px rgba(0, 0, 0, 0.5)' : '0 4px 12px rgba(0, 0, 0, 0.1)',
      width: isModal ? '100%' : '450px',
      maxWidth: '480px',
      margin: isModal ? '0' : '2rem auto',
      transition: 'background-color 0.3s ease, box-shadow 0.3s ease',
      position: 'relative',
    },
    title: {
      color: isDarkMode ? '#e0e0e0' : '#333',
      marginBottom: '1.5rem',
      fontSize: '1.125rem',
      fontWeight: '600',
      letterSpacing: '-0.02em',
    },
    formGroup: {
      width: '100%',
      marginBottom: '1.25rem',
    },
    label: {
      display: 'block',
      marginBottom: '0.5rem',
      color: isDarkMode ? '#e0e0e0' : '#1f2937',
      textAlign: 'left',
      fontSize: '0.875rem',
      fontWeight: '500',
      letterSpacing: '-0.01em',
    },
    select: {
      width: '100%',
      padding: '0.75rem 0.875rem',
      fontSize: '0.875rem',
      fontWeight: '400',
      borderRadius: '8px',
      border: `1px solid ${isDarkMode ? '#444' : '#d1d5db'}`,
      backgroundColor: isDarkMode ? '#2a2a2a' : '#fff',
      color: isDarkMode ? '#e0e0e0' : '#1f2937',
      transition: 'background-color 0.3s ease, border-color 0.3s ease, color 0.3s ease',
      cursor: 'pointer',
      fontFamily: 'Inter, sans-serif',
    },
    uploadButton: {
      width: '100%',
      padding: '0.875rem',
      fontSize: '0.875rem',
      fontWeight: '400',
      border: `2px dashed ${isDarkMode ? '#555' : '#d1d5db'}`,
      borderRadius: '8px',
      backgroundColor: isDarkMode ? '#2a2a2a' : '#f9fafb',
      color: isDarkMode ? '#d0d0d0' : '#6b7280',
      cursor: 'pointer',
      marginBottom: '1.5rem',
      transition: 'background-color 0.3s ease, border-color 0.3s ease, color 0.3s ease',
      fontFamily: 'Inter, sans-serif',
    },
    startButton: {
      width: '100%',
      padding: '0.75rem 1rem',
      fontSize: '0.875rem',
      fontWeight: '600',
      color: isDarkMode ? '#ffffff' : '#000000',
      backgroundColor: isDarkMode ? '#2d2d2d' : '#ffffff',
      borderWidth: '1px',
      borderStyle: 'solid',
      borderColor: isDarkMode ? '#3d3d3d' : '#e5e5e5',
      borderRadius: '8px',
      cursor: 'pointer',
      transition: 'all 0.3s ease',
      fontFamily: 'Inter, sans-serif',
      letterSpacing: '-0.01em',
      marginTop: '0.5rem',
    },
    startButtonHover: {
      backgroundColor: isDarkMode ? '#3d3d3d' : '#f5f5f5',
      borderColor: isDarkMode ? '#4d4d4d' : '#d5d5d5',
    },
    startButtonDisabled: {
      cursor: 'not-allowed',
      opacity: 0.6,
    },
    fileInput: {
      display: 'none',
    },
    fileName: {
      marginTop: '0.5rem',
      fontSize: '0.8125rem',
      color: isDarkMode ? '#9ca3af' : '#6b7280',
      fontStyle: 'italic',
    },
    errorMessage: {
      color: '#dc3545',
      fontSize: '0.8125rem',
      marginBottom: '0.75rem',
      textAlign: 'center',
    },
    closeButton: {
      position: 'absolute',
      top: '1rem',
      right: '1rem',
      width: '34px',
      height: '34px',
      borderRadius: '10px',
      border: 'none',
      backgroundColor: isDarkMode ? '#2a2a2a' : '#f4f4f5',
      color: isDarkMode ? '#d1d5db' : '#4b5563',
      cursor: 'pointer',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      transition: 'background-color 0.2s ease, color 0.2s ease',
      boxShadow: isDarkMode ? '0 1px 2px rgba(0, 0, 0, 0.25)' : '0 1px 2px rgba(15, 23, 42, 0.1)',
    },
    closeButtonHover: {
      backgroundColor: isDarkMode ? '#383838' : '#e4e4e7',
      color: isDarkMode ? '#f4f4f5' : '#1f2937',
    },
    closeIcon: {
      width: '16px',
      height: '16px',
    },
  };

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      setSelectedFile(file);
      setUploadError(null);
      handleFileUpload(file);
    }
  };

  const handleFileUpload = async (file) => {
    setIsUploading(true);
    setUploadError(null);
    
    try {
      const result = await apiService.uploadResume(file, jobRole);
      setResumeId(result.resume_id);
      setIsUploading(false);
    } catch (error) {
      setUploadError(error.message || 'Failed to upload resume');
      setIsUploading(false);
      setSelectedFile(null);
    }
  };

  const handleStartClick = async () => {
    if (!resumeId) {
      setUploadError('Please upload a resume first');
      return;
    }
    if (!jobRole) {
      setUploadError('Please select a job role');
      return;
    }

    try {
      await onStartInterview(resumeId, jobRole);
    } catch (error) {
      setUploadError(error.message || 'Failed to start interview');
    }
  };

  const isStartDisabled = !resumeId || isUploading;

  return (
    <div style={styles.container}>
      {onClose && (
        <button
          type="button"
          style={{
            ...styles.closeButton,
            ...(isCloseHovered ? styles.closeButtonHover : {}),
          }}
          onClick={onClose}
          aria-label="Close setup"
          onMouseEnter={() => setIsCloseHovered(true)}
          onMouseLeave={() => setIsCloseHovered(false)}
        >
          <svg viewBox="0 0 16 16" fill="none" style={styles.closeIcon}>
            <path d="M12 4L4 12M4 4l8 8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </button>
      )}
      {uploadError && (
        <div style={styles.errorMessage}>{uploadError}</div>
      )}

      <div style={styles.formGroup}>
        <label style={styles.label}>Upload Resume</label>
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileSelect}
          accept=".pdf,.docx"
          style={styles.fileInput}
        />
        <button 
          style={styles.uploadButton}
          onClick={() => fileInputRef.current?.click()}
          disabled={isUploading}
        >
          {isUploading ? 'Uploading...' : selectedFile ? selectedFile.name : 'Click to upload...'}
        </button>
        {selectedFile && !isUploading && (
          <div style={styles.fileName}>✓ Resume uploaded successfully</div>
        )}
      </div>

      <div style={styles.formGroup}>
        <label htmlFor="jobRole" style={styles.label}>Select Job Role</label>
        <select
          id="jobRole"
          style={styles.select}
          value={jobRole}
          onChange={(e) => setJobRole(e.target.value)}
          disabled={isUploading}
        >
          <option value="Data Scientist">Data Scientist</option>
          <option value="Software Engineer">Software Engineer</option>
          <option value="Data Engineer">Data Engineer</option>
          <option value="ML Engineer">ML Engineer</option>
        </select>
      </div>

      <button
          style={{
            ...styles.startButton,
            ...(isStartDisabled ? styles.startButtonDisabled : {}),
            ...(!isStartDisabled && isStartHovered ? styles.startButtonHover : {}),
          }}
          onClick={handleStartClick}
          disabled={isStartDisabled}
          onMouseEnter={() => {
            if (!isStartDisabled) {
              setIsStartHovered(true);
            }
          }}
          onMouseLeave={() => setIsStartHovered(false)}
      >
        {isUploading ? 'Processing...' : 'Start Interview'}
      </button>
    </div>
  );
}

export default SetupScreen;


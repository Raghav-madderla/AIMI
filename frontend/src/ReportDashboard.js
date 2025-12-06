import React, { useEffect, useRef, useState } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  RadialLinearScale,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { Radar, Bar, Line, Doughnut } from 'react-chartjs-2';
import * as THREE from 'three';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  RadialLinearScale,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const ReportDashboard = ({ report, isDarkMode, onClose }) => {
  const threeContainerRef = useRef(null);
  const [expandedQuestion, setExpandedQuestion] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');

  // Theme colors
  const theme = {
    bg: isDarkMode ? '#0f0f0f' : '#f8fafc',
    cardBg: isDarkMode ? '#1a1a2e' : '#ffffff',
    cardBorder: isDarkMode ? '#2a2a4a' : '#e2e8f0',
    text: isDarkMode ? '#e2e8f0' : '#1e293b',
    textSecondary: isDarkMode ? '#94a3b8' : '#64748b',
    accent: '#6366f1',
    success: '#10b981',
    warning: '#f59e0b',
    danger: '#ef4444',
    gradient: isDarkMode 
      ? 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)'
      : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
  };

  // Three.js 3D Score Visualization
  useEffect(() => {
    if (!threeContainerRef.current || !report?.executive_summary) return;

    const container = threeContainerRef.current;
    const width = container.clientWidth;
    const height = 180;

    // Scene setup
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setSize(width, height);
    renderer.setClearColor(0x000000, 0);
    container.appendChild(renderer.domElement);

    // Create score ring
    const score = report.executive_summary.overall_score || 0;
    const ringGeometry = new THREE.TorusGeometry(2, 0.3, 16, 100, Math.PI * 2 * score);
    const ringMaterial = new THREE.MeshBasicMaterial({ 
      color: score >= 0.7 ? 0x10b981 : score >= 0.5 ? 0xf59e0b : 0xef4444 
    });
    const ring = new THREE.Mesh(ringGeometry, ringMaterial);
    scene.add(ring);

    // Background ring
    const bgRingGeometry = new THREE.TorusGeometry(2, 0.2, 16, 100);
    const bgRingMaterial = new THREE.MeshBasicMaterial({ 
      color: isDarkMode ? 0x2a2a4a : 0xe2e8f0,
      transparent: true,
      opacity: 0.3
    });
    const bgRing = new THREE.Mesh(bgRingGeometry, bgRingMaterial);
    scene.add(bgRing);

    // Particles
    const particlesGeometry = new THREE.BufferGeometry();
    const particlesCount = 40;
    const positions = new Float32Array(particlesCount * 3);
    
    for (let i = 0; i < particlesCount * 3; i++) {
      positions[i] = (Math.random() - 0.5) * 10;
    }
    
    particlesGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    const particlesMaterial = new THREE.PointsMaterial({
      size: 0.04,
      color: 0x6366f1,
      transparent: true,
      opacity: 0.5
    });
    const particles = new THREE.Points(particlesGeometry, particlesMaterial);
    scene.add(particles);

    camera.position.z = 5;

    // Animation
    let animationId;
    const animate = () => {
      animationId = requestAnimationFrame(animate);
      ring.rotation.z += 0.003;
      bgRing.rotation.z -= 0.001;
      particles.rotation.y += 0.0005;
      renderer.render(scene, camera);
    };
    animate();

    return () => {
      cancelAnimationFrame(animationId);
      container.removeChild(renderer.domElement);
      renderer.dispose();
    };
  }, [report, isDarkMode]);

  if (!report) {
    return <div style={{ color: theme.text, padding: '2rem' }}>Loading report...</div>;
  }

  const { 
    executive_summary, 
    metric_breakdown, 
    domain_analysis, 
    difficulty_performance,
    questions_breakdown,
    insights,
    score_progression
  } = report;

  // Performance level text without emoji
  const getPerformanceLevelText = (level) => {
    const levelMap = {
      'Outstanding': 'OUTSTANDING',
      'Excellent': 'EXCELLENT',
      'Strong': 'STRONG',
      'Good': 'GOOD',
      'Developing': 'DEVELOPING',
      'Needs Work': 'NEEDS IMPROVEMENT'
    };
    return levelMap[level] || level?.toUpperCase() || 'N/A';
  };

  // Chart configurations
  const radarData = {
    labels: domain_analysis?.domains_list || [],
    datasets: [{
      label: 'Performance',
      data: (domain_analysis?.scores_list || []).map(s => s * 100),
      backgroundColor: 'rgba(99, 102, 241, 0.2)',
      borderColor: '#6366f1',
      borderWidth: 2,
      pointBackgroundColor: '#6366f1',
      pointBorderColor: '#fff',
      pointHoverBackgroundColor: '#fff',
      pointHoverBorderColor: '#6366f1'
    }]
  };

  const radarOptions = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      r: {
        beginAtZero: true,
        max: 100,
        ticks: { 
          stepSize: 20,
          color: theme.textSecondary,
          backdropColor: 'transparent'
        },
        grid: { color: isDarkMode ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)' },
        angleLines: { color: isDarkMode ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)' },
        pointLabels: { 
          color: theme.text,
          font: { size: 11, weight: '500' }
        }
      }
    },
    plugins: {
      legend: { display: false }
    }
  };

  const difficultyData = {
    labels: ['Easy', 'Medium', 'Hard'],
    datasets: [{
      label: 'Score %',
      data: [
        (difficulty_performance?.easy?.score || 0) * 100,
        (difficulty_performance?.medium?.score || 0) * 100,
        (difficulty_performance?.hard?.score || 0) * 100
      ],
      backgroundColor: ['#10b981', '#f59e0b', '#ef4444'],
      borderRadius: 8,
      borderSkipped: false
    }]
  };

  const barOptions = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      y: { 
        beginAtZero: true, 
        max: 100,
        ticks: { color: theme.textSecondary },
        grid: { color: isDarkMode ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)' }
      },
      x: { 
        ticks: { color: theme.textSecondary },
        grid: { display: false }
      }
    },
    plugins: {
      legend: { display: false }
    }
  };

  const progressionData = {
    labels: score_progression?.scores?.map(s => `Q${s.question_number}`) || [],
    datasets: [{
      label: 'Score',
      data: (score_progression?.scores || []).map(s => s.score * 100),
      borderColor: '#6366f1',
      backgroundColor: 'rgba(99, 102, 241, 0.1)',
      fill: true,
      tension: 0.4,
      pointBackgroundColor: '#6366f1',
      pointBorderColor: '#fff',
      pointRadius: 6,
      pointHoverRadius: 8
    }]
  };

  const lineOptions = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      y: { 
        beginAtZero: true, 
        max: 100,
        ticks: { color: theme.textSecondary },
        grid: { color: isDarkMode ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)' }
      },
      x: { 
        ticks: { color: theme.textSecondary },
        grid: { display: false }
      }
    },
    plugins: {
      legend: { display: false }
    }
  };

  const metricDoughnutData = {
    labels: ['Technical', 'Completeness', 'Clarity'],
    datasets: [{
      data: [
        (metric_breakdown?.technical_accuracy?.score || 0) * 100,
        (metric_breakdown?.completeness?.score || 0) * 100,
        (metric_breakdown?.clarity?.score || 0) * 100
      ],
      backgroundColor: ['#6366f1', '#10b981', '#f59e0b'],
      borderWidth: 0,
      cutout: '60%'
    }]
  };

  const getScoreColor = (score) => {
    if (score >= 0.8) return theme.success;
    if (score >= 0.6) return theme.warning;
    return theme.danger;
  };

  const getTrendText = (trend) => {
    switch(trend) {
      case 'improving': return 'IMPROVING';
      case 'declining': return 'DECLINING';
      case 'consistent': return 'CONSISTENT';
      default: return 'N/A';
    }
  };

  const styles = {
    container: {
      minHeight: '100vh',
      backgroundColor: theme.bg,
      padding: '2rem',
      fontFamily: "'Inter', -apple-system, sans-serif"
    },
    header: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      marginBottom: '2rem',
      paddingBottom: '1rem',
      borderBottom: `1px solid ${theme.cardBorder}`
    },
    title: {
      color: theme.text,
      fontSize: '1.75rem',
      fontWeight: '700',
      margin: 0,
      letterSpacing: '-0.02em'
    },
    subtitle: {
      color: theme.textSecondary,
      fontSize: '0.875rem',
      marginTop: '0.25rem'
    },
    closeButton: {
      padding: '0.75rem 1.5rem',
      backgroundColor: theme.accent,
      color: '#fff',
      border: 'none',
      borderRadius: '8px',
      cursor: 'pointer',
      fontWeight: '600',
      fontSize: '0.875rem',
      transition: 'transform 0.2s, box-shadow 0.2s',
      boxShadow: '0 4px 14px rgba(99, 102, 241, 0.3)'
    },
    tabs: {
      display: 'flex',
      gap: '0.5rem',
      marginBottom: '2rem',
      backgroundColor: theme.cardBg,
      padding: '0.5rem',
      borderRadius: '12px',
      border: `1px solid ${theme.cardBorder}`
    },
    tab: {
      padding: '0.75rem 1.5rem',
      border: 'none',
      borderRadius: '8px',
      cursor: 'pointer',
      fontWeight: '500',
      transition: 'all 0.2s',
      fontSize: '0.875rem'
    },
    grid: {
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))',
      gap: '1.5rem'
    },
    card: {
      backgroundColor: theme.cardBg,
      borderRadius: '16px',
      padding: '1.5rem',
      border: `1px solid ${theme.cardBorder}`,
      boxShadow: isDarkMode 
        ? '0 4px 20px rgba(0, 0, 0, 0.3)' 
        : '0 4px 20px rgba(0, 0, 0, 0.05)',
      textAlign: 'left'
    },
    cardTitle: {
      color: theme.text,
      fontSize: '1rem',
      fontWeight: '600',
      marginBottom: '1rem',
      display: 'flex',
      alignItems: 'center',
      gap: '0.5rem',
      textTransform: 'uppercase',
      letterSpacing: '0.05em'
    },
    scoreCircle: {
      width: '130px',
      height: '130px',
      borderRadius: '50%',
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'center',
      alignItems: 'center',
      margin: '1rem auto',
      border: `5px solid ${getScoreColor(executive_summary?.overall_score || 0)}`,
      backgroundColor: isDarkMode ? 'rgba(255,255,255,0.02)' : 'rgba(0,0,0,0.02)'
    },
    bigScore: {
      fontSize: '2.25rem',
      fontWeight: '700',
      color: theme.text
    },
    performanceLevel: {
      display: 'inline-flex',
      alignItems: 'center',
      gap: '0.5rem',
      padding: '0.5rem 1rem',
      backgroundColor: isDarkMode ? 'rgba(99, 102, 241, 0.15)' : 'rgba(99, 102, 241, 0.1)',
      borderRadius: '6px',
      color: theme.accent,
      fontWeight: '600',
      fontSize: '0.75rem',
      marginTop: '1rem',
      letterSpacing: '0.1em'
    },
    metricBar: {
      marginBottom: '1rem'
    },
    metricLabel: {
      display: 'flex',
      justifyContent: 'space-between',
      marginBottom: '0.5rem',
      color: theme.text,
      fontSize: '0.875rem'
    },
    progressBar: {
      height: '8px',
      backgroundColor: isDarkMode ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
      borderRadius: '4px',
      overflow: 'hidden'
    },
    progressFill: {
      height: '100%',
      borderRadius: '4px',
      transition: 'width 1s ease-out'
    },
    insightCard: {
      padding: '1rem',
      backgroundColor: isDarkMode ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.02)',
      borderRadius: '12px',
      marginBottom: '1rem',
      textAlign: 'left'
    },
    insightTitle: {
      color: theme.text,
      fontWeight: '600',
      fontSize: '0.8rem',
      marginBottom: '0.75rem',
      display: 'flex',
      alignItems: 'center',
      gap: '0.5rem',
      textTransform: 'uppercase',
      letterSpacing: '0.05em',
      textAlign: 'left'
    },
    insightList: {
      listStyle: 'none',
      padding: 0,
      margin: 0,
      textAlign: 'left'
    },
    insightItem: {
      color: theme.text,
      fontSize: '0.875rem',
      marginBottom: '0.5rem',
      paddingLeft: '1.25rem',
      position: 'relative',
      lineHeight: '1.5',
      textAlign: 'left'
    },
    questionCard: {
      backgroundColor: isDarkMode ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.02)',
      borderRadius: '12px',
      marginBottom: '0.75rem',
      overflow: 'hidden',
      border: `1px solid ${theme.cardBorder}`,
      cursor: 'pointer',
      transition: 'all 0.2s'
    },
    questionHeader: {
      padding: '1rem',
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center'
    },
    questionContent: {
      padding: '0 1rem 1rem 1rem',
      borderTop: `1px solid ${theme.cardBorder}`
    },
    badge: {
      padding: '0.25rem 0.75rem',
      borderRadius: '4px',
      fontSize: '0.7rem',
      fontWeight: '600',
      textTransform: 'uppercase',
      letterSpacing: '0.05em'
    },
    threeContainer: {
      width: '100%',
      height: '180px',
      marginBottom: '0.5rem'
    },
    chartContainer: {
      height: '250px',
      marginTop: '1rem'
    },
    sectionIcon: {
      width: '20px',
      height: '20px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      backgroundColor: isDarkMode ? 'rgba(99, 102, 241, 0.2)' : 'rgba(99, 102, 241, 0.1)',
      borderRadius: '4px',
      color: theme.accent
    }
  };

  // Icon components
  const ChartIcon = () => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M18 20V10M12 20V4M6 20v-6"/>
    </svg>
  );

  const TargetIcon = () => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>
    </svg>
  );

  const TrendIcon = () => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/>
    </svg>
  );

  const ListIcon = () => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/>
      <line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/>
    </svg>
  );

  const CheckIcon = () => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <polyline points="20 6 9 17 4 12"/>
    </svg>
  );

  const ArrowUpIcon = () => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <line x1="12" y1="19" x2="12" y2="5"/><polyline points="5 12 12 5 19 12"/>
    </svg>
  );

  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <div>
          <h1 style={styles.title}>Interview Performance Report</h1>
          <p style={styles.subtitle}>
            {report.job_role} Position | {new Date(report.generated_at || Date.now()).toLocaleDateString()}
          </p>
        </div>
        <button 
          style={styles.closeButton}
          onClick={onClose}
          onMouseEnter={(e) => {
            e.target.style.transform = 'translateY(-2px)';
            e.target.style.boxShadow = '0 6px 20px rgba(99, 102, 241, 0.4)';
          }}
          onMouseLeave={(e) => {
            e.target.style.transform = 'translateY(0)';
            e.target.style.boxShadow = '0 4px 14px rgba(99, 102, 241, 0.3)';
          }}
        >
          Back to Interview
        </button>
      </div>

      {/* Tabs */}
      <div style={styles.tabs}>
        {['overview', 'details', 'insights'].map((tab) => (
          <button
            key={tab}
            style={{
              ...styles.tab,
              backgroundColor: activeTab === tab ? theme.accent : 'transparent',
              color: activeTab === tab ? '#fff' : theme.textSecondary
            }}
            onClick={() => setActiveTab(tab)}
          >
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </button>
        ))}
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <div style={styles.grid}>
          {/* Executive Summary Card */}
          <div style={{ ...styles.card, gridColumn: 'span 1' }}>
            <h3 style={styles.cardTitle}>
              <span style={styles.sectionIcon}><TargetIcon /></span>
              Executive Summary
            </h3>
            <div ref={threeContainerRef} style={styles.threeContainer}></div>
            <div style={{ textAlign: 'center' }}>
              <div style={styles.scoreCircle}>
                <span style={styles.bigScore}>{executive_summary?.overall_percentage || 0}%</span>
              </div>
              <div style={styles.performanceLevel}>
                {getPerformanceLevelText(executive_summary?.performance_level)}
              </div>
              <p style={{ color: theme.textSecondary, marginTop: '1rem', fontSize: '0.875rem' }}>
                {executive_summary?.total_questions} questions completed
              </p>
            </div>
          </div>

          {/* Metric Breakdown Card */}
          <div style={styles.card}>
            <h3 style={styles.cardTitle}>
              <span style={styles.sectionIcon}><ChartIcon /></span>
              Core Metrics
            </h3>
            <div style={{ height: '180px', marginBottom: '1.5rem' }}>
              <Doughnut data={metricDoughnutData} options={{ 
                responsive: true, 
                maintainAspectRatio: false,
                plugins: { 
                  legend: { 
                    position: 'bottom',
                    labels: { color: theme.text, padding: 15, font: { size: 11 } }
                  }
                }
              }} />
            </div>
            {Object.entries(metric_breakdown || {}).map(([key, metric]) => (
              <div key={key} style={styles.metricBar}>
                <div style={styles.metricLabel}>
                  <span>{metric.label}</span>
                  <span style={{ fontWeight: '600' }}>{Math.round(metric.score * 100)}%</span>
                </div>
                <div style={styles.progressBar}>
                  <div style={{
                    ...styles.progressFill,
                    width: `${metric.score * 100}%`,
                    backgroundColor: getScoreColor(metric.score)
                  }}></div>
                </div>
              </div>
            ))}
          </div>

          {/* Domain Radar Card */}
          <div style={styles.card}>
            <h3 style={styles.cardTitle}>
              <span style={styles.sectionIcon}><TargetIcon /></span>
              Domain Performance
            </h3>
            <div style={styles.chartContainer}>
              <Radar data={radarData} options={radarOptions} />
            </div>
            <div style={{ marginTop: '1rem', display: 'flex', gap: '0.75rem', justifyContent: 'center', flexWrap: 'wrap' }}>
              {domain_analysis?.strongest && (
                <span style={{ ...styles.badge, backgroundColor: 'rgba(16, 185, 129, 0.15)', color: theme.success }}>
                  STRONGEST: {domain_analysis.strongest}
                </span>
              )}
              {domain_analysis?.weakest && domain_analysis.weakest !== domain_analysis.strongest && (
                <span style={{ ...styles.badge, backgroundColor: 'rgba(239, 68, 68, 0.15)', color: theme.danger }}>
                  FOCUS AREA: {domain_analysis.weakest}
                </span>
              )}
            </div>
          </div>

          {/* Difficulty Performance Card */}
          <div style={styles.card}>
            <h3 style={styles.cardTitle}>
              <span style={styles.sectionIcon}><ChartIcon /></span>
              Difficulty Breakdown
            </h3>
            <div style={styles.chartContainer}>
              <Bar data={difficultyData} options={barOptions} />
            </div>
          </div>

          {/* Score Progression Card */}
          <div style={{ ...styles.card, gridColumn: '1 / -1' }}>
            <h3 style={styles.cardTitle}>
              <span style={styles.sectionIcon}><TrendIcon /></span>
              Score Progression
              <span style={{ 
                ...styles.badge, 
                marginLeft: '0.75rem',
                backgroundColor: score_progression?.trend === 'improving' 
                  ? 'rgba(16, 185, 129, 0.15)' 
                  : score_progression?.trend === 'declining'
                  ? 'rgba(239, 68, 68, 0.15)'
                  : 'rgba(99, 102, 241, 0.15)',
                color: score_progression?.trend === 'improving' 
                  ? theme.success 
                  : score_progression?.trend === 'declining'
                  ? theme.danger
                  : theme.accent
              }}>
                {getTrendText(score_progression?.trend)}
              </span>
            </h3>
            <div style={{ height: '200px' }}>
              <Line data={progressionData} options={lineOptions} />
            </div>
          </div>
        </div>
      )}

      {/* Details Tab */}
      {activeTab === 'details' && (
        <div style={styles.card}>
          <h3 style={styles.cardTitle}>
            <span style={styles.sectionIcon}><ListIcon /></span>
            Question-by-Question Analysis
          </h3>
          {questions_breakdown?.map((q, index) => (
            <div 
              key={index} 
              style={{
                ...styles.questionCard,
                borderLeft: `4px solid ${getScoreColor(q.score)}`
              }}
              onClick={() => setExpandedQuestion(expandedQuestion === index ? null : index)}
            >
              <div style={styles.questionHeader}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <span style={{ 
                    color: theme.textSecondary, 
                    fontSize: '0.75rem',
                    fontWeight: '600',
                    minWidth: '28px'
                  }}>
                    Q{q.index}
                  </span>
                  <span style={{ color: theme.text, fontWeight: '500', fontSize: '0.875rem' }}>
                    {q.domain}
                  </span>
                  <span style={{ 
                    ...styles.badge, 
                    backgroundColor: q.difficulty === 'easy' ? 'rgba(16, 185, 129, 0.15)' :
                                    q.difficulty === 'medium' ? 'rgba(245, 158, 11, 0.15)' :
                                    'rgba(239, 68, 68, 0.15)',
                    color: q.difficulty === 'easy' ? theme.success :
                           q.difficulty === 'medium' ? theme.warning :
                           theme.danger
                  }}>
                    {q.difficulty?.toUpperCase()}
                  </span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                  <span style={{ 
                    color: getScoreColor(q.score), 
                    fontWeight: '700',
                    fontSize: '1rem'
                  }}>
                    {Math.round(q.score * 100)}%
                  </span>
                  <span style={{ color: theme.textSecondary, fontSize: '0.875rem' }}>
                    {expandedQuestion === index ? '−' : '+'}
                  </span>
                </div>
              </div>
              
              {expandedQuestion === index && (
                <div style={styles.questionContent}>
                  <div style={{ marginBottom: '1rem', marginTop: '1rem' }}>
                    <p style={{ color: theme.textSecondary, fontSize: '0.75rem', marginBottom: '0.25rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Question</p>
                    <p style={{ color: theme.text, fontSize: '0.875rem', lineHeight: '1.5' }}>{q.question}</p>
                  </div>
                  <div style={{ marginBottom: '1rem' }}>
                    <p style={{ color: theme.textSecondary, fontSize: '0.75rem', marginBottom: '0.25rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Your Response</p>
                    <p style={{ color: theme.text, fontSize: '0.875rem', lineHeight: '1.5' }}>{q.answer}</p>
                  </div>
                  <div style={{ 
                    display: 'grid', 
                    gridTemplateColumns: 'repeat(3, 1fr)', 
                    gap: '0.5rem',
                    marginBottom: '1rem'
                  }}>
                    <div style={{ textAlign: 'center', padding: '0.75rem', backgroundColor: isDarkMode ? 'rgba(99, 102, 241, 0.1)' : 'rgba(99, 102, 241, 0.05)', borderRadius: '8px' }}>
                      <div style={{ color: theme.accent, fontWeight: '600' }}>{Math.round(q.technical_accuracy * 100)}%</div>
                      <div style={{ color: theme.textSecondary, fontSize: '0.7rem', textTransform: 'uppercase' }}>Technical</div>
                    </div>
                    <div style={{ textAlign: 'center', padding: '0.75rem', backgroundColor: isDarkMode ? 'rgba(16, 185, 129, 0.1)' : 'rgba(16, 185, 129, 0.05)', borderRadius: '8px' }}>
                      <div style={{ color: theme.success, fontWeight: '600' }}>{Math.round(q.completeness * 100)}%</div>
                      <div style={{ color: theme.textSecondary, fontSize: '0.7rem', textTransform: 'uppercase' }}>Completeness</div>
                    </div>
                    <div style={{ textAlign: 'center', padding: '0.75rem', backgroundColor: isDarkMode ? 'rgba(245, 158, 11, 0.1)' : 'rgba(245, 158, 11, 0.05)', borderRadius: '8px' }}>
                      <div style={{ color: theme.warning, fontWeight: '600' }}>{Math.round(q.clarity * 100)}%</div>
                      <div style={{ color: theme.textSecondary, fontSize: '0.7rem', textTransform: 'uppercase' }}>Clarity</div>
                    </div>
                  </div>
                  {q.feedback && (
                    <div style={{ 
                      padding: '0.75rem', 
                      backgroundColor: isDarkMode ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.02)',
                      borderRadius: '8px',
                      borderLeft: `3px solid ${theme.accent}`,
                      fontSize: '0.875rem',
                      color: theme.textSecondary,
                      lineHeight: '1.5'
                    }}>
                      <span style={{ fontWeight: '500', color: theme.text }}>Feedback: </span>
                      {q.feedback}
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Insights Tab */}
      {activeTab === 'insights' && (
        <div style={styles.grid}>
          {/* Summary */}
          <div style={{ ...styles.card, gridColumn: '1 / -1' }}>
            <h3 style={styles.cardTitle}>
              <span style={styles.sectionIcon}><ListIcon /></span>
              Overall Assessment
            </h3>
            <p style={{ color: theme.text, fontSize: '0.95rem', lineHeight: '1.8', textAlign: 'left' }}>
              {insights?.overall_summary || 'No summary available.'}
            </p>
          </div>

          {/* Strengths */}
          <div style={styles.card}>
            <div style={styles.insightCard}>
              <div style={{ ...styles.insightTitle, color: theme.success }}>
                <CheckIcon /> Key Strengths
              </div>
              <ul style={styles.insightList}>
                {(insights?.strengths || []).map((s, i) => (
                  <li key={i} style={styles.insightItem}>
                    <span style={{ position: 'absolute', left: 0, color: theme.success }}>•</span>
                    {s}
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Improvements */}
          <div style={styles.card}>
            <div style={styles.insightCard}>
              <div style={{ ...styles.insightTitle, color: theme.warning }}>
                <ArrowUpIcon /> Areas for Development
              </div>
              <ul style={styles.insightList}>
                {(insights?.areas_for_improvement || []).map((s, i) => (
                  <li key={i} style={styles.insightItem}>
                    <span style={{ position: 'absolute', left: 0, color: theme.warning }}>•</span>
                    {s}
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Recommendations */}
          <div style={{ ...styles.card, gridColumn: '1 / -1' }}>
            <div style={styles.insightCard}>
              <div style={{ ...styles.insightTitle, color: theme.accent }}>
                <TargetIcon /> Recommendations
              </div>
              <ul style={styles.insightList}>
                {(insights?.recommendations || []).map((s, i) => (
                  <li key={i} style={styles.insightItem}>
                    <span style={{ position: 'absolute', left: 0, color: theme.accent }}>{i + 1}.</span>
                    {s}
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Hiring Recommendation */}
          {insights?.hiring_recommendation && (
            <div style={{ ...styles.card, gridColumn: '1 / -1' }}>
              <h3 style={styles.cardTitle}>
                <span style={styles.sectionIcon}><CheckIcon /></span>
                Hiring Assessment
              </h3>
              <div style={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: '1.5rem',
                padding: '1.25rem',
                backgroundColor: isDarkMode ? 'rgba(99, 102, 241, 0.08)' : 'rgba(99, 102, 241, 0.05)',
                borderRadius: '12px',
                border: `1px solid ${theme.cardBorder}`
              }}>
                <div style={{
                  padding: '0.875rem 1.25rem',
                  backgroundColor: insights.hiring_recommendation.decision?.includes('Recommend') 
                    ? theme.success 
                    : insights.hiring_recommendation.decision === 'Consider'
                    ? theme.warning
                    : theme.danger,
                  color: '#fff',
                  borderRadius: '6px',
                  fontWeight: '700',
                  fontSize: '0.875rem',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em'
                }}>
                  {insights.hiring_recommendation.decision}
                </div>
                <div style={{ flex: 1, textAlign: 'left' }}>
                  <div style={{ color: theme.textSecondary, fontSize: '0.75rem', marginBottom: '0.25rem', textTransform: 'uppercase', letterSpacing: '0.05em', textAlign: 'left' }}>
                    Confidence: {Math.round((insights.hiring_recommendation.confidence || 0) * 100)}%
                  </div>
                  <div style={{ color: theme.text, fontSize: '0.9rem', lineHeight: '1.5', textAlign: 'left' }}>
                    {insights.hiring_recommendation.reasoning}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ReportDashboard;

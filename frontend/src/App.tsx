import { useState, useEffect } from 'react';

function App() {
  const [longUrl, setLongUrl] = useState<string>('');
  const [shortUrl, setShortUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  // Analytics state
  const [analyticsUrl, setAnalyticsUrl] = useState<string>('');
  const [clicks, setClicks] = useState<number | null>(null);
  const [analyticsError, setAnalyticsError] = useState<string | null>(null);
  const [isAnalyticsLoading, setIsAnalyticsLoading] = useState<boolean>(false);

  // Create floating particles on component mount
  useEffect(() => {
    createParticles();
  }, []);

  const createParticles = () => {
    const particlesContainer = document.getElementById('particles');
    if (!particlesContainer) return;
    
    const particleCount = 50;
    
    for (let i = 0; i < particleCount; i++) {
      const particle = document.createElement('div');
      particle.className = 'particle';
      particle.style.left = Math.random() * 100 + '%';
      particle.style.top = Math.random() * 100 + '%';
      particle.style.animationDelay = Math.random() * 6 + 's';
      particle.style.animationDuration = (Math.random() * 3 + 3) + 's';
      particlesContainer.appendChild(particle);
    }
  };

  const handleSubmit = async (e: any) => {
    e.preventDefault?.();
    if (!longUrl.trim()) return;
    
    setIsLoading(true);
    setShortUrl(null);
    setError(null);

    try {
      const response = await fetch('/api/links', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          long_url: longUrl,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to shorten URL');
      }

      const data = await response.json();
      const fullShortUrl = window.location.origin + data.short_url;
      setShortUrl(fullShortUrl);
    } catch (err: any) {
      setError(err.message || 'An unexpected error occurred.');
    } finally {
      setIsLoading(false);
      setLongUrl('');
    }
  };

  const handleAnalyticsSubmit = async (e: any) => {
    e.preventDefault?.();
    if (!analyticsUrl.trim()) return;
    
    setIsAnalyticsLoading(true);
    setClicks(null);
    setAnalyticsError(null);

    try {
      // Strip trailing slash and extract the ID
      let cleanUrl = analyticsUrl.trim();
      if (cleanUrl.endsWith('/')) {
        cleanUrl = cleanUrl.slice(0, -1);
      }
      
      const urlParts = cleanUrl.split('/');
      const shortId = urlParts[urlParts.length - 1];
      
      if (!shortId) {
        throw new Error('Invalid URL format');
      }

      const response = await fetch(`/api/analytics/${shortId}`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch analytics');
      }

      const data = await response.json();
      
      if (typeof data.clicks !== 'number') {
        throw new Error('The URL is wrong');
      }
      
      setClicks(data.clicks);
    } catch (err: any) {
      setAnalyticsError(err.message === 'Failed to fetch analytics' ? 'The URL is wrong' : err.message);
    } finally {
      setIsAnalyticsLoading(false);
    }
  };

  // Add click ripple effect
  const handleClick = (e: React.MouseEvent) => {
    const ripple = document.createElement('div');
    ripple.style.position = 'fixed';
    ripple.style.left = e.clientX + 'px';
    ripple.style.top = e.clientY + 'px';
    ripple.style.width = '20px';
    ripple.style.height = '20px';
    ripple.style.background = 'radial-gradient(circle, rgba(100, 108, 255, 0.6) 0%, transparent 70%)';
    ripple.style.borderRadius = '50%';
    ripple.style.pointerEvents = 'none';
    ripple.style.transform = 'translate(-50%, -50%)';
    ripple.style.animation = 'ripple 0.6s ease-out forwards';
    ripple.style.zIndex = '9999';
    
    document.body.appendChild(ripple);
    
    setTimeout(() => {
      ripple.remove();
    }, 600);
  };

  return (
    <div style={styles.app} onClick={handleClick}>
      <div style={styles.particles} id="particles"></div>
      
      <div style={styles.container}>
        {/* URL Shortener Card */}
        <div style={styles.card}>
          <h1 style={styles.title}>URL Shortener</h1>
          <p style={styles.subtitle}>
            Transform long URLs into sleek, shareable links with our modern microservices architecture
          </p>
          
          <div style={styles.form}>
            <input
              type="url"
              value={longUrl}
              onChange={(e) => setLongUrl(e.target.value)}
              placeholder="Enter a URL to transform..."
              disabled={isLoading}
              style={styles.input}
              onKeyPress={(e) => {
                if (e.key === 'Enter' && longUrl.trim()) {
                  handleSubmit(e as any);
                }
              }}
            />
            <button onClick={handleSubmit} disabled={isLoading || !longUrl.trim()} style={styles.button}>
              {isLoading ? (
                <>
                  <span style={styles.spinner}></span>
                  Shortening...
                </>
              ) : (
                'Shorten'
              )}
            </button>
          </div>

          {shortUrl && (
            <div style={styles.result}>
              <p style={styles.resultText}>✨ Your shortened URL is ready:</p>
              <div style={styles.resultContainer}>
                <a 
                  href={shortUrl} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  style={styles.shortUrlLink}
                >
                  {shortUrl}
                </a>
              </div>
            </div>
          )}

          {error && (
            <div style={styles.error}>
              <p>Error: {error}</p>
            </div>
          )}
        </div>

        {/* Analytics Card */}
        <div style={styles.card}>
          <h1 style={styles.title}>Check Clicks</h1>
          <p style={styles.subtitle}>
            Take a look at how many times your shortened link has been used!
          </p>
          
          <div style={styles.form}>
            <input
              type="url"
              value={analyticsUrl}
              onChange={(e) => setAnalyticsUrl(e.target.value)}
              placeholder="Enter your shortened URL..."
              disabled={isAnalyticsLoading}
              style={styles.input}
              onKeyPress={(e) => {
                if (e.key === 'Enter' && analyticsUrl.trim()) {
                  handleAnalyticsSubmit(e as any);
                }
              }}
            />
            <button onClick={handleAnalyticsSubmit} disabled={isAnalyticsLoading || !analyticsUrl.trim()} style={styles.button}>
              {isAnalyticsLoading ? (
                <>
                  <span style={styles.spinner}></span>
                  Checking...
                </>
              ) : (
                'Check'
              )}
            </button>
          </div>

          {clicks !== null && (
            <div style={styles.analyticsResult}>
              <p style={styles.resultText}>📊 Click Analytics:</p>
              <div style={styles.clicksDisplay}>
                <span style={styles.clicksNumber}>{clicks.toLocaleString()}</span>
                <span style={styles.clicksLabel}>total clicks</span>
              </div>
            </div>
          )}

          {analyticsError && (
            <div style={styles.error}>
              <p>Error: {analyticsError}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

const styles = {
  app: {
    fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
    background: 'linear-gradient(135deg, #0f0f0f 0%, #1a1a1a 100%)',
    color: '#ffffff',
    minHeight: '100vh',
    minWidth: '100vw',
    position: 'relative' as const,
    zIndex: 1,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '2rem',
  },

  particles: {
    position: 'fixed' as const,
    top: 0,
    left: 0,
    width: '100%',
    height: '100%',
    pointerEvents: 'none' as const,
    zIndex: 0,
  },

  container: {
    display: 'flex',
    gap: '2rem',
    maxWidth: '1200px',
    width: '100%',
    flexWrap: 'wrap' as const,
    justifyContent: 'center',
  },

  card: {
    background: 'rgba(20, 20, 20, 0.8)',
    backdropFilter: 'blur(20px)',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    borderRadius: '24px',
    padding: '3rem',
    maxWidth: '600px',
    width: '100%',
    textAlign: 'center' as const,
    boxShadow: '0 20px 40px rgba(0, 0, 0, 0.3), 0 0 80px rgba(100, 108, 255, 0.1)',
    position: 'relative' as const,
    overflow: 'hidden',
    animation: 'slideUp 0.8s ease-out',
  },

  title: {
    fontSize: '3rem',
    fontWeight: 800,
    background: 'linear-gradient(135deg, #646cff 0%, #61dafb 50%, #a855f7 100%)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
    backgroundClip: 'text',
    marginBottom: '1rem',
    letterSpacing: '-2px',
    position: 'relative' as const,
    zIndex: 2,
  },

  subtitle: {
    fontSize: '1.2rem',
    color: '#a0a0a0',
    marginBottom: '2.5rem',
    lineHeight: 1.6,
    position: 'relative' as const,
    zIndex: 2,
  },

  form: {
    display: 'flex',
    gap: '1rem',
    marginBottom: '2rem',
    position: 'relative' as const,
    zIndex: 2,
    flexDirection: 'column' as const,
  },

  input: {
    flex: 1,
    padding: '1rem 1.5rem',
    background: 'rgba(40, 40, 40, 0.8)',
    border: '2px solid rgba(255, 255, 255, 0.1)',
    borderRadius: '16px',
    color: '#ffffff',
    fontSize: '1rem',
    outline: 'none',
    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
    backdropFilter: 'blur(10px)',
  },

  button: {
    padding: '1rem 2rem',
    background: 'linear-gradient(135deg, #646cff 0%, #7c3aed 100%)',
    border: 'none',
    borderRadius: '16px',
    color: 'white',
    fontSize: '1rem',
    fontWeight: 600,
    cursor: 'pointer',
    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
    position: 'relative' as const,
    overflow: 'hidden',
    minWidth: '140px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '0.5rem',
  },

  spinner: {
    display: 'inline-block',
    width: '20px',
    height: '20px',
    border: '2px solid rgba(255, 255, 255, 0.3)',
    borderRadius: '50%',
    borderTop: '2px solid #ffffff',
    animation: 'spin 1s linear infinite',
  },

  result: {
    background: 'rgba(34, 197, 94, 0.1)',
    border: '1px solid rgba(34, 197, 94, 0.3)',
    borderRadius: '16px',
    padding: '1.5rem',
    marginBottom: '1rem',
    animation: 'fadeInScale 0.5s ease-out',
    position: 'relative' as const,
    zIndex: 2,
  },

  analyticsResult: {
    background: 'rgba(59, 130, 246, 0.1)',
    border: '1px solid rgba(59, 130, 246, 0.3)',
    borderRadius: '16px',
    padding: '1.5rem',
    marginBottom: '1rem',
    animation: 'fadeInScale 0.5s ease-out',
    position: 'relative' as const,
    zIndex: 2,
  },

  resultText: {
    color: '#22c55e',
    marginBottom: '1rem',
    fontWeight: 600,
  },

  resultContainer: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexWrap: 'wrap' as const,
    gap: '0.5rem',
  },

  shortUrlLink: {
    color: '#60a5fa',
    textDecoration: 'none',
    fontFamily: "'Monaco', 'Courier New', monospace",
    background: 'rgba(96, 165, 250, 0.1)',
    padding: '0.5rem 1rem',
    borderRadius: '8px',
    display: 'inline-block',
    transition: 'all 0.3s ease',
    wordBreak: 'break-all' as const,
    maxWidth: '300px',
  },

  copyBtn: {
    background: 'rgba(96, 165, 250, 0.2)',
    border: '1px solid rgba(96, 165, 250, 0.3)',
    color: '#60a5fa',
    padding: '0.5rem 1rem',
    borderRadius: '8px',
    fontSize: '0.9rem',
    cursor: 'pointer',
    transition: 'all 0.3s ease',
    minWidth: '70px',
  },

  copySuccess: {
    background: 'rgba(34, 197, 94, 0.2)',
    borderColor: 'rgba(34, 197, 94, 0.3)',
    color: '#22c55e',
  },

  clicksDisplay: {
    display: 'flex',
    flexDirection: 'column' as const,
    alignItems: 'center',
    gap: '0.5rem',
  },

  clicksNumber: {
    fontSize: '2.5rem',
    fontWeight: 800,
    color: '#3b82f6',
    textShadow: '0 0 20px rgba(59, 130, 246, 0.5)',
  },

  clicksLabel: {
    fontSize: '1rem',
    color: '#94a3b8',
    textTransform: 'uppercase' as const,
    letterSpacing: '1px',
  },

  error: {
    background: 'rgba(239, 68, 68, 0.1)',
    border: '1px solid rgba(239, 68, 68, 0.3)',
    borderRadius: '16px',
    padding: '1.5rem',
    animation: 'shake 0.5s ease-out',
    position: 'relative' as const,
    zIndex: 2,
    color: '#ef4444',
    fontWeight: 600,
  },
};

// Add CSS animations
const styleSheet = document.createElement('style');
styleSheet.textContent = `
  .particle {
    position: absolute;
    width: 2px;
    height: 2px;
    background: linear-gradient(45deg, #646cff, #61dafb);
    border-radius: 50%;
    animation: float 6s ease-in-out infinite;
    opacity: 0.6;
  }

  @keyframes float {
    0%, 100% { 
      transform: translateY(0px) rotate(0deg); 
      opacity: 0.6; 
    }
    50% { 
      transform: translateY(-20px) rotate(180deg); 
      opacity: 1; 
    }
  }

  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }

  @keyframes slideUp {
    from { 
      transform: translateY(50px); 
      opacity: 0; 
    }
    to { 
      transform: translateY(0); 
      opacity: 1; 
    }
  }

  @keyframes fadeInScale {
    from {
      opacity: 0;
      transform: scale(0.9);
    }
    to {
      opacity: 1;
      transform: scale(1);
    }
  }

  @keyframes shake {
    0%, 100% { transform: translateX(0); }
    25% { transform: translateX(-5px); }
    75% { transform: translateX(5px); }
  }

  @keyframes ripple {
    to {
      transform: translate(-50%, -50%) scale(4);
      opacity: 0;
    }
  }

  @media (max-width: 768px) {
    .container {
      flex-direction: column;
      align-items: center;
    }
  }
`;
document.head.appendChild(styleSheet);

export default App;
/**
 * FolderStatus component
 * Shows current folder status and provides Refresh button to trigger manual scan.
 */
import { useState, useEffect, useRef } from 'react';
import { getFolderSettings, triggerScan, getScanStatus, FolderSettings, ScanJobStatus } from '../api';

export default function FolderStatus() {
  const [settings, setSettings] = useState<FolderSettings | null>(null);
  const [scanning, setScanning] = useState(false);
  const [jobStatus, setJobStatus] = useState<ScanJobStatus | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pollCount, setPollCount] = useState(0);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  // Load settings and check for ongoing scan
  useEffect(() => {
    loadSettings();
    
    // Check if there's an ongoing scan from previous session
    const savedJobId = localStorage.getItem('currentScanJobId');
    if (savedJobId) {
      checkSavedJob(savedJobId);
    }
  }, []);

  // Poll for job status when scanning
  useEffect(() => {
    if (!jobStatus || jobStatus.status !== 'running') {
      // Clean up interval if job is not running
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      return;
    }

    // Clear any existing interval
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }

    // Start polling
    intervalRef.current = setInterval(async () => {
      try {
        console.log(`Polling scan status... (attempt ${pollCount + 1})`);
        const status = await getScanStatus(jobStatus.job_id);
        setJobStatus(status);
        setPollCount(prev => prev + 1);
        
        if (status.status !== 'running') {
          setScanning(false);
          localStorage.removeItem('currentScanJobId');
          
          if (intervalRef.current) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
          }
          
          if (status.status === 'completed') {
            setMessage(
              `✅ Scan complete! ${status.new_files || 0} new/changed files, ${status.skipped_files || 0} skipped.`
            );
            setError(null);
          } else if (status.status === 'failed') {
            setError(`❌ Scan failed: ${status.errors?.join(', ') || 'Unknown error'}`);
            setMessage(null);
          }
        } else {
          // Update progress message
          setMessage(`⏳ Scanning in progress... (${pollCount + 1} checks)`);
        }
      } catch (err) {
        console.error('Failed to poll scan status:', err);
        setError(`Failed to check scan status: ${err}`);
        
        // Stop polling after too many failures
        if (pollCount > 30) { // 60 seconds of failures
          if (intervalRef.current) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
          }
          setScanning(false);
          setError('Scan status check timed out. Please check backend logs.');
        }
      }
    }, 2000); // Poll every 2 seconds

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [jobStatus, pollCount]);

  async function loadSettings() {
    try {
      const data = await getFolderSettings();
      setSettings(data);
    } catch (err) {
      console.error('Failed to load settings:', err);
      setError(`Failed to load settings: ${err}`);
    }
  }

  async function checkSavedJob(jobId: string) {
    try {
      console.log('Checking saved job:', jobId);
      const status = await getScanStatus(jobId);
      
      if (status.status === 'running') {
        setScanning(true);
        setJobStatus(status);
        setMessage('⏳ Resuming scan from previous session...');
      } else {
        localStorage.removeItem('currentScanJobId');
      }
    } catch (err) {
      console.error('Failed to check saved job:', err);
      localStorage.removeItem('currentScanJobId');
    }
  }

  async function handleRefresh() {
    if (!settings) {
      setError('Settings not loaded. Please refresh the page.');
      return;
    }

    try {
      setScanning(true);
      setMessage('🚀 Starting scan...');
      setError(null);
      setJobStatus(null);
      setPollCount(0);

      console.log('Triggering scan with path:', settings.folder_path);

      const response = await triggerScan({
        path: settings.folder_path,
        include_subfolders: settings.include_subfolders,
      });

      console.log('Scan triggered, job_id:', response.job_id);
      setMessage(`✅ Scan started! Job ID: ${response.job_id}`);
      
      // Save job ID to localStorage for persistence
      localStorage.setItem('currentScanJobId', response.job_id);
      
      // Wait a moment for backend to process
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Start polling for status
      const status = await getScanStatus(response.job_id);
      console.log('Initial status:', status);
      setJobStatus(status);
      
    } catch (err) {
      console.error('Failed to trigger scan:', err);
      setError(`❌ Failed to trigger scan: ${err}`);
      setMessage(null);
      setScanning(false);
      localStorage.removeItem('currentScanJobId');
    }
  }

  function handleCancel() {
    // Stop polling
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    
    // Clear state
    setScanning(false);
    setJobStatus(null);
    setMessage('❌ Scan cancelled');
    setPollCount(0);
    localStorage.removeItem('currentScanJobId');
    
    console.log('Scan cancelled by user');
  }

  return (
    <div style={{ padding: '20px', maxWidth: '600px', borderBottom: '1px solid #ddd' }}>
      <h3>Folder Status</h3>

      {settings && (
        <div style={{ marginBottom: '15px' }}>
          <p>
            <strong>Folder:</strong> {settings.folder_path}
          </p>
          <p>
            <strong>Include subfolders:</strong> {settings.include_subfolders ? 'Yes' : 'No'}
          </p>
        </div>
      )}

      {!settings && !error && (
        <p style={{ color: '#666', fontSize: '14px' }}>Loading settings...</p>
      )}

      <div style={{ display: 'flex', gap: '10px' }}>
        {!scanning ? (
          <button
            onClick={handleRefresh}
            disabled={!settings}
            style={{
              padding: '10px 20px',
              fontSize: '14px',
              cursor: !settings ? 'not-allowed' : 'pointer',
              backgroundColor: '#28a745',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              opacity: !settings ? 0.6 : 1,
            }}
          >
            🔄 Scan Folder
          </button>
        ) : (
          <button
            onClick={handleCancel}
            style={{
              padding: '10px 20px',
              fontSize: '14px',
              cursor: 'pointer',
              backgroundColor: '#dc3545',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
            }}
          >
            ⏹ Cancel Scan
          </button>
        )}
      </div>

      {error && (
        <div
          style={{
            marginTop: '15px',
            padding: '12px',
            backgroundColor: '#f8d7da',
            color: '#721c24',
            border: '1px solid #f5c6cb',
            borderRadius: '4px',
            fontSize: '14px',
          }}
        >
          <strong>Error:</strong> {error}
          <br />
          <small>Check that:</small>
          <ul style={{ margin: '8px 0 0 20px', padding: 0 }}>
            <li>Backend is running (http://localhost:8000)</li>
            <li>RQ worker is running</li>
            <li>Folder path exists and is accessible</li>
          </ul>
        </div>
      )}

      {message && !error && (
        <div
          style={{
            marginTop: '15px',
            padding: '12px',
            backgroundColor: scanning ? '#fff3cd' : '#d4edda',
            color: scanning ? '#856404' : '#155724',
            border: `1px solid ${scanning ? '#ffeeba' : '#c3e6cb'}`,
            borderRadius: '4px',
            fontSize: '14px',
          }}
        >
          {message}
        </div>
      )}

      {jobStatus && (
        <div 
          style={{ 
            marginTop: '15px', 
            padding: '12px',
            backgroundColor: '#f8f9fa',
            border: '1px solid #dee2e6',
            borderRadius: '4px',
            fontSize: '13px'
          }}
        >
          <p style={{ margin: '0 0 8px 0' }}><strong>Job Details:</strong></p>
          <p style={{ margin: '4px 0' }}>
            <strong>Job ID:</strong> <code>{jobStatus.job_id}</code>
          </p>
          <p style={{ margin: '4px 0' }}>
            <strong>Status:</strong> 
            <span style={{ 
              marginLeft: '8px',
              padding: '2px 8px',
              borderRadius: '12px',
              backgroundColor: jobStatus.status === 'running' ? '#ffc107' : 
                             jobStatus.status === 'completed' ? '#28a745' : '#dc3545',
              color: 'white',
              fontSize: '12px'
            }}>
              {jobStatus.status.toUpperCase()}
            </span>
          </p>
          <p style={{ margin: '4px 0' }}>
            <strong>Scan Path:</strong> {jobStatus.scan_path}
          </p>
          
          {jobStatus.status === 'completed' && (
            <div style={{ marginTop: '12px', paddingTop: '12px', borderTop: '1px solid #dee2e6' }}>
              <p style={{ margin: '4px 0', color: '#28a745' }}>
                ✅ New/Changed files: <strong>{jobStatus.new_files || 0}</strong>
              </p>
              <p style={{ margin: '4px 0', color: '#6c757d' }}>
                ⏭️ Skipped files: <strong>{jobStatus.skipped_files || 0}</strong>
              </p>
              {jobStatus.error_count && jobStatus.error_count > 0 && (
                <>
                  <p style={{ margin: '4px 0', color: '#dc3545' }}>
                    ❌ Errors: <strong>{jobStatus.error_count}</strong>
                  </p>
                  {jobStatus.errors && jobStatus.errors.length > 0 && (
                    <div style={{ marginTop: '8px', fontSize: '12px' }}>
                      <strong>Error details:</strong>
                      <ul style={{ margin: '4px 0 0 20px', padding: 0 }}>
                        {jobStatus.errors.map((err, idx) => (
                          <li key={idx} style={{ color: '#dc3545' }}>{err}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </>
              )}
            </div>
          )}
          
          {jobStatus.status === 'running' && (
            <p style={{ margin: '8px 0 0 0', fontSize: '12px', color: '#666' }}>
              ⏳ Polling for updates... ({pollCount} checks)
            </p>
          )}
        </div>
      )}

      <details style={{ marginTop: '15px', fontSize: '12px', color: '#666' }}>
        <summary style={{ cursor: 'pointer', fontWeight: 'bold' }}>
          💡 Troubleshooting Tips
        </summary>
        <div style={{ marginTop: '8px', paddingLeft: '12px' }}>
          <p><strong>If scan is stuck:</strong></p>
          <ol style={{ margin: '4px 0 0 20px' }}>
            <li>Check backend logs: <code>tail -f logs/backend.log</code></li>
            <li>Check worker logs: <code>tail -f logs/worker.log</code></li>
            <li>Verify Redis is running: <code>redis-cli ping</code></li>
            <li>Check RQ worker: <code>rq info</code></li>
          </ol>
          <p style={{ marginTop: '8px' }}><strong>Folder path tips:</strong></p>
          <ul style={{ margin: '4px 0 0 20px' }}>
            <li>Use absolute paths: <code>/Users/yourname/Downloads</code></li>
            <li>Avoid <code>~</code> - use full path instead</li>
            <li>Ensure folder exists and has PDF files</li>
          </ul>
        </div>
      </details>
    </div>
  );
}


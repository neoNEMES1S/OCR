/**
 * FolderStatus component
 * Shows current folder status and provides Refresh button to trigger manual scan.
 */
import { useState, useEffect } from 'react';
import { getFolderSettings, triggerScan, getScanStatus, FolderSettings, ScanJobStatus } from '../api';

export default function FolderStatus() {
  const [settings, setSettings] = useState<FolderSettings | null>(null);
  const [scanning, setScanning] = useState(false);
  const [jobStatus, setJobStatus] = useState<ScanJobStatus | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    loadSettings();
  }, []);

  // Poll for job status when scanning
  useEffect(() => {
    if (!jobStatus || jobStatus.status !== 'running') {
      return;
    }

    const interval = setInterval(async () => {
      try {
        const status = await getScanStatus(jobStatus.job_id);
        setJobStatus(status);
        
        if (status.status !== 'running') {
          setScanning(false);
          
          if (status.status === 'completed') {
            setMessage(
              `Scan complete! ${status.new_files || 0} new/changed files, ${status.skipped_files || 0} skipped.`
            );
          } else {
            setMessage(`Scan ${status.status}: ${status.errors?.join(', ') || 'Unknown error'}`);
          }
        }
      } catch (error) {
        console.error('Failed to poll scan status:', error);
      }
    }, 2000); // Poll every 2 seconds

    return () => clearInterval(interval);
  }, [jobStatus]);

  async function loadSettings() {
    try {
      const data = await getFolderSettings();
      setSettings(data);
    } catch (error) {
      console.error('Failed to load settings:', error);
    }
  }

  async function handleRefresh() {
    if (!settings) return;

    try {
      setScanning(true);
      setMessage(null);
      setJobStatus(null);

      const response = await triggerScan({
        path: settings.folder_path,
        include_subfolders: settings.include_subfolders,
      });

      setMessage(`Scan started: ${response.message}`);
      
      // Start polling for status
      const status = await getScanStatus(response.job_id);
      setJobStatus(status);
    } catch (error) {
      setMessage(`Failed to trigger scan: ${error}`);
      setScanning(false);
    }
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

      <button
        onClick={handleRefresh}
        disabled={scanning || !settings}
        style={{
          padding: '10px 20px',
          fontSize: '14px',
          cursor: scanning || !settings ? 'not-allowed' : 'pointer',
          backgroundColor: '#28a745',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
        }}
      >
        {scanning ? 'Scanning...' : 'Refresh / Rescan'}
      </button>

      {message && (
        <div
          style={{
            marginTop: '15px',
            padding: '10px',
            backgroundColor: '#e9ecef',
            borderRadius: '4px',
            fontSize: '14px',
          }}
        >
          {message}
        </div>
      )}

      {jobStatus && (
        <div style={{ marginTop: '15px', fontSize: '13px' }}>
          <p><strong>Job ID:</strong> {jobStatus.job_id}</p>
          <p><strong>Status:</strong> {jobStatus.status}</p>
          {jobStatus.status === 'completed' && (
            <>
              <p>New/Changed files: {jobStatus.new_files || 0}</p>
              <p>Skipped files: {jobStatus.skipped_files || 0}</p>
              {jobStatus.error_count && jobStatus.error_count > 0 && (
                <p style={{ color: '#d9534f' }}>Errors: {jobStatus.error_count}</p>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}


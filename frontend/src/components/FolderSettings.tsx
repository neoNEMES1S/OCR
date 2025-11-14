/**
 * FolderSettings component
 * Allows users to configure the auto-ingest folder path and options.
 */
import { useState, useEffect } from 'react';
import { getFolderSettings, updateFolderSettings, FolderSettings as IFolderSettings } from '../api';

// Detect operating system for path suggestions
function getOS() {
  const userAgent = window.navigator.userAgent.toLowerCase();
  if (userAgent.includes('win')) return 'windows';
  if (userAgent.includes('mac')) return 'mac';
  if (userAgent.includes('linux')) return 'linux';
  return 'unknown';
}

// Get default path suggestions based on OS
function getDefaultPaths(os: string): string[] {
  switch (os) {
    case 'windows':
      return [
        'C:\\Users\\Public\\Documents\\PDFs',
        'C:\\PDFs',
        '%USERPROFILE%\\Documents\\PDFs',
      ];
    case 'mac':
      return [
        '/Users/Shared/PDFs',
        '~/Documents/PDFs',
        '~/Desktop/PDFs',
        '/tmp/pdfs',
      ];
    case 'linux':
      return [
        '/home/shared/pdfs',
        '~/Documents/pdfs',
        '/tmp/pdfs',
      ];
    default:
      return ['/tmp/pdfs', '~/Documents/PDFs'];
  }
}

export default function FolderSettings() {
  const [settings, setSettings] = useState<IFolderSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const [folderPath, setFolderPath] = useState('');
  const [includeSubfolders, setIncludeSubfolders] = useState(false);
  const [autoIngest, setAutoIngest] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);
  
  const os = getOS();
  const suggestions = getDefaultPaths(os);

  useEffect(() => {
    loadSettings();
  }, []);

  async function loadSettings() {
    try {
      setLoading(true);
      const data = await getFolderSettings();
      setSettings(data);
      setFolderPath(data.folder_path);
      setIncludeSubfolders(data.include_subfolders);
      setAutoIngest(data.auto_ingest);
    } catch (error) {
      setMessage({ type: 'error', text: `Failed to load settings: ${error}` });
    } finally {
      setLoading(false);
    }
  }

  async function handleSave() {
    try {
      setSaving(true);
      setMessage(null);
      
      const updated = await updateFolderSettings({
        folder_path: folderPath,
        include_subfolders: includeSubfolders,
        auto_ingest: autoIngest,
      });
      
      setSettings(updated);
      setMessage({ type: 'success', text: 'Settings saved successfully!' });
    } catch (error) {
      setMessage({ type: 'error', text: `Failed to save: ${error}` });
    } finally {
      setSaving(false);
    }
  }

  async function handleBrowseFolder() {
    try {
      // Check if File System Access API is supported
      if ('showDirectoryPicker' in window) {
        // @ts-ignore - File System Access API
        const dirHandle = await window.showDirectoryPicker();
        
        // Note: This gives us a handle, but we need the actual path
        // The browser can't give us the full path for security reasons
        setMessage({ 
          type: 'error', 
          text: 'Browser security prevents accessing folder paths. Please enter the path manually or ensure backend has access to the folder.' 
        });
        
        // Show the name at least
        setFolderPath(dirHandle.name);
      } else {
        setMessage({ 
          type: 'error', 
          text: 'Folder picker not supported in this browser. Please enter the path manually.' 
        });
      }
    } catch (error) {
      if (error instanceof Error && error.name !== 'AbortError') {
        setMessage({ type: 'error', text: `Failed to browse: ${error.message}` });
      }
    }
  }

  function handleSuggestionClick(path: string) {
    setFolderPath(path);
    setShowSuggestions(false);
  }

  if (loading) {
    return <div>Loading settings...</div>;
  }

  return (
    <div style={{ padding: '20px', maxWidth: '600px' }}>
      <h2>Folder Settings</h2>
      
      <div style={{ marginBottom: '15px' }}>
        <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
          Folder Path:
        </label>
        <div style={{ display: 'flex', gap: '10px', marginBottom: '8px' }}>
          <input
            type="text"
            value={folderPath}
            onChange={(e) => setFolderPath(e.target.value)}
            onFocus={() => setShowSuggestions(true)}
            placeholder={suggestions[0]}
            style={{ flex: 1, padding: '8px', fontSize: '14px' }}
          />
          <button
            onClick={handleBrowseFolder}
            style={{
              padding: '8px 16px',
              fontSize: '14px',
              cursor: 'pointer',
              backgroundColor: '#6c757d',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
            }}
            title="Browse for folder (local backend only)"
          >
            📁 Browse
          </button>
          <button
            onClick={() => setShowSuggestions(!showSuggestions)}
            style={{
              padding: '8px 16px',
              fontSize: '14px',
              cursor: 'pointer',
              backgroundColor: '#17a2b8',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
            }}
            title="Show path suggestions"
          >
            💡
          </button>
        </div>
        
        {showSuggestions && (
          <div style={{
            border: '1px solid #ddd',
            borderRadius: '4px',
            backgroundColor: '#f8f9fa',
            padding: '10px',
            marginTop: '8px',
          }}>
            <div style={{ fontSize: '12px', fontWeight: 'bold', marginBottom: '8px', color: '#666' }}>
              Suggested paths for {os === 'mac' ? 'macOS' : os === 'windows' ? 'Windows' : 'Linux'}:
            </div>
            {suggestions.map((path, idx) => (
              <div
                key={idx}
                onClick={() => handleSuggestionClick(path)}
                style={{
                  padding: '6px 10px',
                  cursor: 'pointer',
                  backgroundColor: 'white',
                  border: '1px solid #dee2e6',
                  borderRadius: '3px',
                  marginBottom: '5px',
                  fontSize: '13px',
                  fontFamily: 'monospace',
                }}
                onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#e9ecef'}
                onMouseOut={(e) => e.currentTarget.style.backgroundColor = 'white'}
              >
                {path}
              </div>
            ))}
            <button
              onClick={() => setShowSuggestions(false)}
              style={{
                marginTop: '8px',
                padding: '4px 8px',
                fontSize: '12px',
                cursor: 'pointer',
                backgroundColor: '#fff',
                border: '1px solid #ddd',
                borderRadius: '3px',
              }}
            >
              Close
            </button>
          </div>
        )}
        
        <div style={{ fontSize: '12px', color: '#666', marginTop: '8px' }}>
          ℹ️ <strong>Important:</strong> The backend server must have access to this folder path.
          {os === 'mac' && ' Use absolute paths like /Users/username/Documents/PDFs'}
          {os === 'windows' && ' Use paths like C:\\Users\\username\\Documents\\PDFs'}
        </div>
      </div>

      <div style={{ marginBottom: '15px' }}>
        <label style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <input
            type="checkbox"
            checked={includeSubfolders}
            onChange={(e) => setIncludeSubfolders(e.target.checked)}
          />
          <span>Include Subfolders</span>
        </label>
      </div>

      <div style={{ marginBottom: '20px' }}>
        <label style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <input
            type="checkbox"
            checked={autoIngest}
            onChange={(e) => setAutoIngest(e.target.checked)}
          />
          <span>Auto-ingest on Startup</span>
        </label>
      </div>

      <button
        onClick={handleSave}
        disabled={saving}
        style={{
          padding: '10px 20px',
          fontSize: '14px',
          cursor: saving ? 'not-allowed' : 'pointer',
          backgroundColor: '#007bff',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
        }}
      >
        {saving ? 'Saving...' : 'Save Settings'}
      </button>

      {message && (
        <div
          style={{
            marginTop: '15px',
            padding: '10px',
            borderRadius: '4px',
            backgroundColor: message.type === 'success' ? '#d4edda' : '#f8d7da',
            color: message.type === 'success' ? '#155724' : '#721c24',
            border: `1px solid ${message.type === 'success' ? '#c3e6cb' : '#f5c6cb'}`,
          }}
        >
          {message.text}
        </div>
      )}

      {settings && (
        <div style={{ marginTop: '20px', fontSize: '12px', color: '#666' }}>
          <p>Current folder: <strong>{settings.folder_path}</strong></p>
          <p>Include subfolders: <strong>{settings.include_subfolders ? 'Yes' : 'No'}</strong></p>
          <p>Auto-ingest: <strong>{settings.auto_ingest ? 'Enabled' : 'Disabled'}</strong></p>
        </div>
      )}
    </div>
  );
}

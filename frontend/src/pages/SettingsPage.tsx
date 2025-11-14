/**
 * SettingsPage
 * Page for configuring folder settings and viewing status.
 */
import FolderSettings from '../components/FolderSettings';
import FolderStatus from '../components/FolderStatus';

export default function SettingsPage() {
  return (
    <div>
      <h1 style={{ padding: '20px', paddingBottom: '10px' }}>Settings</h1>
      <FolderStatus />
      <FolderSettings />
    </div>
  );
}


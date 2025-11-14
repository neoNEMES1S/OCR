/**
 * SettingsPage
 * Page for configuring folder settings and viewing status.
 */
import FolderSettings from '../components/FolderSettings';
import FolderStatus from '../components/FolderStatus';
import FileUpload from '../components/FileUpload';

export default function SettingsPage() {
  return (
    <div>
      <h1 style={{ padding: '20px', paddingBottom: '10px' }}>Settings & Upload</h1>
      <FileUpload />
      <FolderStatus />
      <FolderSettings />
    </div>
  );
}


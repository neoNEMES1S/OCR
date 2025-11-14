/**
 * Main App component with routing
 */
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import SearchPage from './pages/SearchPage';
import SettingsPage from './pages/SettingsPage';

function App() {
  return (
    <Router>
      <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
        {/* Navigation */}
        <nav
          style={{
            backgroundColor: '#343a40',
            color: 'white',
            padding: '15px 20px',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
          }}
        >
          <div style={{ display: 'flex', gap: '20px', alignItems: 'center' }}>
            <h1 style={{ margin: 0, fontSize: '20px' }}>OCR PDF Search</h1>
            <div style={{ display: 'flex', gap: '15px' }}>
              <Link
                to="/"
                style={{
                  color: 'white',
                  textDecoration: 'none',
                  padding: '5px 10px',
                  borderRadius: '4px',
                  backgroundColor: 'rgba(255,255,255,0.1)',
                }}
              >
                Search
              </Link>
              <Link
                to="/settings"
                style={{
                  color: 'white',
                  textDecoration: 'none',
                  padding: '5px 10px',
                  borderRadius: '4px',
                  backgroundColor: 'rgba(255,255,255,0.1)',
                }}
              >
                Settings
              </Link>
            </div>
          </div>
        </nav>

        {/* Main content */}
        <main style={{ flex: 1, backgroundColor: '#f5f5f5' }}>
          <Routes>
            <Route path="/" element={<SearchPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </main>

        {/* Footer */}
        <footer
          style={{
            backgroundColor: '#f8f9fa',
            padding: '15px 20px',
            textAlign: 'center',
            borderTop: '1px solid #dee2e6',
            color: '#6c757d',
            fontSize: '14px',
          }}
        >
          <p style={{ margin: 0 }}>
            OCR PDF Search - MVP | Backend: FastAPI | Frontend: React + TypeScript
          </p>
        </footer>
      </div>
    </Router>
  );
}

function NotFound() {
  return (
    <div style={{ padding: '40px', textAlign: 'center' }}>
      <h2>404 - Page Not Found</h2>
      <p>The page you're looking for doesn't exist.</p>
      <Link to="/" style={{ color: '#007bff' }}>
        Go to Search
      </Link>
    </div>
  );
}

export default App;


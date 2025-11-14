/**
 * Main App component with routing
 */
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import HomePage from './pages/HomePage';
import SearchPage from './pages/SearchPage';
import SettingsPage from './pages/SettingsPage';

function App() {
  return (
    <Router>
      <div className="min-h-screen flex flex-col">
        {/* Navigation */}
        <nav className="bg-slate-800 text-white shadow-lg">
          <div className="container mx-auto px-4 py-3">
            <div className="flex gap-6 items-center">
              <h1 className="text-xl font-bold">🔍 OCR PDF Search</h1>
              <div className="flex gap-4">
                <Link
                  to="/"
                  className="text-white hover:text-slate-200 px-3 py-2 rounded-md hover:bg-slate-700 transition-colors"
                >
                  Home
                </Link>
                <Link
                  to="/search"
                  className="text-white hover:text-slate-200 px-3 py-2 rounded-md hover:bg-slate-700 transition-colors"
                >
                  Search
                </Link>
                <Link
                  to="/settings"
                  className="text-white hover:text-slate-200 px-3 py-2 rounded-md hover:bg-slate-700 transition-colors"
                >
                  Settings
                </Link>
              </div>
            </div>
          </div>
        </nav>

        {/* Main content */}
        <main className="flex-1">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/search" element={<SearchPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </main>

        {/* Footer */}
        <footer className="bg-slate-100 py-4 text-center border-t border-slate-200 text-slate-600 text-sm">
          <p className="m-0">
            OCR PDF Search - MVP | Backend: FastAPI | Frontend: React + TypeScript + Tailwind
          </p>
        </footer>
      </div>
    </Router>
  );
}

function NotFound() {
  return (
    <div className="p-10 text-center">
      <h2 className="text-2xl font-bold mb-4">404 - Page Not Found</h2>
      <p className="mb-4">The page you're looking for doesn't exist.</p>
      <Link to="/" className="text-blue-600 hover:underline">
        Go to Home
      </Link>
    </div>
  );
}

export default App;


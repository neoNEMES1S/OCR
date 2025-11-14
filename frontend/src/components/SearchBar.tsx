/**
 * SearchBar component
 * Provides search input with toggle between keyword and semantic search.
 */
import { useState } from 'react';

interface SearchBarProps {
  onSearch: (query: string, searchType: 'keyword' | 'semantic') => void;
  loading?: boolean;
}

export default function SearchBar({ onSearch, loading = false }: SearchBarProps) {
  const [query, setQuery] = useState('');
  const [searchType, setSearchType] = useState<'keyword' | 'semantic'>('keyword');

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (query.trim()) {
      onSearch(query.trim(), searchType);
    }
  }

  return (
    <div style={{ padding: '20px', borderBottom: '1px solid #ddd' }}>
      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: '10px' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
            <span style={{ fontWeight: 'bold' }}>Search Type:</span>
            <label style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
              <input
                type="radio"
                value="keyword"
                checked={searchType === 'keyword'}
                onChange={(e) => setSearchType(e.target.value as 'keyword' | 'semantic')}
              />
              <span>Keyword (Full-text)</span>
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
              <input
                type="radio"
                value="semantic"
                checked={searchType === 'semantic'}
                onChange={(e) => setSearchType(e.target.value as 'keyword' | 'semantic')}
              />
              <span>Semantic (AI)</span>
            </label>
          </label>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={
              searchType === 'keyword'
                ? 'Enter keywords to search...'
                : 'Enter natural language query...'
            }
            style={{
              flex: 1,
              padding: '10px',
              fontSize: '14px',
              border: '1px solid #ccc',
              borderRadius: '4px',
            }}
          />
          <button
            type="submit"
            disabled={loading || !query.trim()}
            style={{
              padding: '10px 20px',
              fontSize: '14px',
              cursor: loading || !query.trim() ? 'not-allowed' : 'pointer',
              backgroundColor: '#007bff',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
            }}
          >
            {loading ? 'Searching...' : 'Search'}
          </button>
        </div>
      </form>

      <div style={{ marginTop: '10px', fontSize: '12px', color: '#666' }}>
        {searchType === 'keyword' ? (
          <p>Keyword search uses full-text indexing for exact matches and phrases.</p>
        ) : (
          <p>Semantic search uses AI to find contextually similar documents.</p>
        )}
      </div>
    </div>
  );
}


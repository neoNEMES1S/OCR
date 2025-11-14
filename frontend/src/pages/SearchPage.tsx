/**
 * SearchPage
 * Page for searching documents with keyword or semantic search.
 */
import { useState } from 'react';
import SearchBar from '../components/SearchBar';
import SearchResults from '../components/SearchResults';
import { searchFullText, searchSemantic, SearchResult } from '../api';

export default function SearchPage() {
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastQuery, setLastQuery] = useState<string>('');
  const [lastSearchType, setLastSearchType] = useState<'keyword' | 'semantic'>('keyword');
  const [totalResults, setTotalResults] = useState<number | undefined>(undefined);

  async function handleSearch(query: string, searchType: 'keyword' | 'semantic') {
    try {
      setLoading(true);
      setError(null);
      setLastQuery(query);
      setLastSearchType(searchType);

      if (searchType === 'keyword') {
        const response = await searchFullText(query, 1, 20);
        setResults(response.results);
        setTotalResults(response.total_results);
      } else {
        const response = await searchSemantic({
          query,
          top_k: 10,
        });
        setResults(response.results);
        setTotalResults(undefined); // Semantic search doesn't return total
      }
    } catch (err) {
      setError(`Search failed: ${err}`);
      setResults([]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <h1 style={{ padding: '20px', paddingBottom: '10px' }}>Search Documents</h1>
      
      <SearchBar onSearch={handleSearch} loading={loading} />

      {error && (
        <div
          style={{
            margin: '20px',
            padding: '15px',
            backgroundColor: '#f8d7da',
            color: '#721c24',
            border: '1px solid #f5c6cb',
            borderRadius: '4px',
          }}
        >
          {error}
        </div>
      )}

      {loading && (
        <div style={{ padding: '20px', textAlign: 'center', color: '#666' }}>
          <p>Searching...</p>
        </div>
      )}

      {!loading && lastQuery && (
        <SearchResults
          results={results}
          query={lastQuery}
          searchType={lastSearchType}
          totalResults={totalResults}
        />
      )}
    </div>
  );
}


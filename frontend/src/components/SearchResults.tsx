/**
 * SearchResults component
 * Displays search results grouped by document/filename.
 */
import { SearchResult } from '../api';

interface SearchResultsProps {
  results: SearchResult[];
  query: string;
  searchType: 'keyword' | 'semantic';
  totalResults?: number;
}

export default function SearchResults({ results, query, searchType, totalResults }: SearchResultsProps) {
  if (results.length === 0) {
    return (
      <div style={{ padding: '20px', textAlign: 'center', color: '#666' }}>
        <p>No results found for "{query}"</p>
      </div>
    );
  }

  // Group results by document
  const groupedResults = results.reduce((acc, result) => {
    const key = `${result.document_id}-${result.filename}`;
    if (!acc[key]) {
      acc[key] = {
        document_id: result.document_id,
        filename: result.filename,
        results: [],
      };
    }
    acc[key].results.push(result);
    return acc;
  }, {} as Record<string, { document_id: number; filename: string; results: SearchResult[] }>);

  return (
    <div style={{ padding: '20px' }}>
      <div style={{ marginBottom: '15px' }}>
        <h3>Search Results</h3>
        <p style={{ color: '#666', fontSize: '14px' }}>
          Found {totalResults !== undefined ? totalResults : results.length} results for "{query}" 
          ({searchType} search)
        </p>
      </div>

      {Object.values(groupedResults).map((group) => (
        <div
          key={`${group.document_id}-${group.filename}`}
          style={{
            marginBottom: '20px',
            border: '1px solid #ddd',
            borderRadius: '4px',
            padding: '15px',
            backgroundColor: '#f9f9f9',
          }}
        >
          <h4 style={{ marginTop: 0, marginBottom: '10px' }}>
            {group.filename}
          </h4>

          {group.results.map((result, idx) => (
            <div
              key={`${result.chunk_id || idx}-${result.page_no}`}
              style={{
                marginBottom: '10px',
                padding: '10px',
                backgroundColor: 'white',
                borderLeft: '3px solid #007bff',
                paddingLeft: '15px',
              }}
            >
              <div style={{ marginBottom: '5px', fontSize: '12px', color: '#666' }}>
                <strong>Page {result.page_no}</strong>
                {result.score !== undefined && (
                  <span style={{ marginLeft: '10px' }}>
                    Score: {result.score.toFixed(3)}
                  </span>
                )}
              </div>
              
              <div
                style={{ fontSize: '14px', lineHeight: '1.6' }}
                dangerouslySetInnerHTML={{ __html: result.snippet }}
              />
              
              <div style={{ marginTop: '10px' }}>
                <button
                  onClick={() => {
                    // TODO: Implement viewer route
                    console.log('Open viewer for document', result.document_id, 'page', result.page_no);
                    alert(`Open viewer for document ${result.document_id}, page ${result.page_no}`);
                  }}
                  style={{
                    padding: '5px 10px',
                    fontSize: '12px',
                    cursor: 'pointer',
                    backgroundColor: '#007bff',
                    color: 'white',
                    border: 'none',
                    borderRadius: '3px',
                  }}
                >
                  Open Page {result.page_no}
                </button>
              </div>
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}


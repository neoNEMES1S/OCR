# OCR PDF Frontend

React + TypeScript frontend for OCR PDF search application.

## Features

- **Folder Settings**: Configure auto-ingest folder path and options
- **Folder Status**: View current folder and trigger manual scans
- **Search**: Full-text keyword search and semantic AI search
- **Results**: Grouped by document with snippets and page links

## Prerequisites

- Node.js 18+ and npm
- Backend API running on `http://localhost:8000`

## Setup

### 1. Install dependencies

```bash
cd frontend
npm install
```

### 2. Start development server

```bash
npm run dev
```

The app will be available at: http://localhost:3000

### 3. Build for production

```bash
npm run build
```

Built files will be in `dist/` directory.

### 4. Preview production build

```bash
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── main.tsx            # Entry point
│   ├── App.tsx             # Main app with routing
│   ├── api.ts              # API client functions
│   ├── components/
│   │   ├── FolderSettings.tsx   # Settings form
│   │   ├── FolderStatus.tsx     # Status display & refresh
│   │   ├── SearchBar.tsx        # Search input
│   │   └── SearchResults.tsx    # Results display
│   └── pages/
│       ├── SearchPage.tsx       # Search page
│       └── SettingsPage.tsx     # Settings page
├── index.html
├── vite.config.ts
├── tsconfig.json
├── package.json
└── README.md
```

## Pages

### Search Page (`/`)

- Search bar with keyword/semantic toggle
- Real-time search results
- Grouped by document with page numbers
- Snippet highlighting (for keyword search)

### Settings Page (`/settings`)

- Current folder status
- Manual refresh/rescan button with progress
- Folder configuration form
- Auto-ingest toggle

## API Integration

The frontend communicates with the backend API via the `api.ts` module:

### Example API Calls

**Get folder settings:**
```typescript
import { getFolderSettings } from './api';

const settings = await getFolderSettings();
console.log(settings.folder_path);
```

**Trigger scan:**
```typescript
import { triggerScan, getScanStatus } from './api';

const response = await triggerScan({ path: '/tmp/pdfs' });
const status = await getScanStatus(response.job_id);
```

**Search:**
```typescript
import { searchFullText, searchSemantic } from './api';

// Keyword search
const results = await searchFullText('invoice', 1, 20);

// Semantic search
const semanticResults = await searchSemantic({
  query: 'contract termination',
  top_k: 10
});
```

## Development

### API Proxy

The Vite dev server is configured to proxy API requests to the backend:

```typescript
// vite.config.ts
proxy: {
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true,
  },
}
```

This allows frontend to call `/api/v1/...` which gets proxied to `http://localhost:8000/api/v1/...`

### Type Safety

All API calls are fully typed with TypeScript interfaces defined in `api.ts`:

- `FolderSettings`
- `ScanRequest`, `ScanResponse`, `ScanJobStatus`
- `SearchResult`
- `FullTextSearchResponse`, `SemanticSearchResponse`

## Styling

Currently using inline styles for simplicity. Consider adding:

- CSS modules
- Tailwind CSS
- Material-UI or similar component library

## TODOs

- [ ] Implement PDF viewer route (`/viewer/:docId`)
- [ ] Add pagination for search results
- [ ] Add loading skeletons
- [ ] Improve error handling and user feedback
- [ ] Add search history
- [ ] Add filters (by date, document type, etc.)
- [ ] Add document management (delete, re-index)
- [ ] Add authentication

## Testing

Add tests with:

```bash
npm install --save-dev @testing-library/react @testing-library/jest-dom vitest
```

## Deployment

### Static hosting (Netlify, Vercel, etc.)

1. Build: `npm run build`
2. Deploy `dist/` directory
3. Configure API base URL for production

### Docker

Create `Dockerfile`:

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=0 /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

Build and run:

```bash
docker build -t ocr-pdf-frontend .
docker run -p 80:80 ocr-pdf-frontend
```

## License

MIT


# Folder Access Guide

Understanding how folder paths work in a web-based OCR application.

## 🔑 Key Concept: Backend Server Access

**Important:** The folder path must be accessible to the **backend server**, not your web browser.

```
┌─────────────┐              ┌─────────────┐
│   Browser   │  HTTP API    │   Backend   │
│  (Frontend) │──────────────│   Server    │
└─────────────┘              └──────┬──────┘
      │                             │
      │                             ▼
      │                      ┌──────────────┐
      │                      │ File System  │
      │                      │  /path/pdfs  │
      └──────────────────────│   (Scans     │
         Shows results       │    PDFs)     │
                            └──────────────┘
```

The browser **never accesses** the folder directly. It only:
1. Sends the folder path to backend
2. Receives search results

## Scenarios & Solutions

### Scenario 1: Local Development (Same Machine)

**Setup:** Backend and frontend both run on your laptop

**Folder Path:** Any local folder
```
Mac:     /Users/yourname/Documents/PDFs
Windows: C:\Users\yourname\Documents\PDFs
```

**How it works:**
- Backend server runs on your machine
- Server can access your local folders
- Frontend in browser talks to local server
- ✅ Everything works!

---

### Scenario 2: Deployed (Vercel + Supabase)

**Setup:** 
- Frontend on Vercel (runs in browser)
- Backend on Supabase/server (runs remotely)

**Folder Path:** Must be on the **server's** filesystem

**Options:**

#### Option A: Server-side Folder
```
Backend server folder: /app/pdfs
You upload PDFs to the server via:
  - SFTP/SSH
  - Admin upload endpoint
  - Cloud storage mount (S3, etc.)
```

#### Option B: Cloud Storage Mount
```
Mount S3/Google Drive to backend:
  /mnt/s3-pdfs → maps to S3 bucket
  Backend scans /mnt/s3-pdfs
```

#### Option C: Upload API (Recommended for Production)

Add a file upload endpoint to your backend:

```python
# backend/app/api/v1/upload.py
from fastapi import UploadFile

@router.post("/upload")
async def upload_pdf(file: UploadFile):
    # Save to server's storage
    save_path = Path(settings.STORAGE_PATH) / file.filename
    with open(save_path, 'wb') as f:
        f.write(await file.read())
    
    # Trigger ingestion
    enqueue_ingest(queue, str(save_path), doc_id)
```

Then users upload via UI instead of browsing folders.

---

### Scenario 3: Mobile Access

**Challenge:** Mobile browsers can't browse server filesystems

**Solutions:**

#### Solution A: Upload Interface (Best for Mobile)

Instead of folder browsing, add drag & drop upload:

```typescript
// Let users upload PDFs directly
<input 
  type="file" 
  accept=".pdf" 
  multiple 
  onChange={handleUpload}
/>
```

#### Solution B: Cloud Integration

Integrate with cloud services:
- Google Drive picker
- Dropbox chooser
- OneDrive picker

Users pick files from cloud → Backend downloads → Processes

---

## Current Implementation

### What Works Now:

1. ✅ **Path suggestions** - Smart suggestions based on OS
2. ✅ **Manual entry** - Type any path the backend can access
3. ✅ **Browse button** - Limited (security restrictions)

### What You Can Do:

**Local development:**
```bash
1. Create folder: mkdir ~/Documents/PDFs
2. Add some PDFs
3. In Settings: Use suggestion "~/Documents/PDFs"
4. Click "Refresh / Rescan"
```

**Production deployment:**
```bash
1. SSH into your backend server
2. Create folder: mkdir /app/pdfs
3. Upload PDFs: scp *.pdf server:/app/pdfs/
4. In Settings: Enter "/app/pdfs"
5. Click "Refresh / Rescan"
```

---

## Recommended Approaches by Use Case

### Personal Use (1 user, local files)
✅ **Run backend locally** + access local folders
```
Backend: localhost:8000
Folder: Your local filesystem
Upload: Not needed (direct access)
```

### Small Team (Internal tool)
✅ **Shared server folder** + SFTP upload
```
Backend: company-server:8000
Folder: /shared/pdfs on server
Upload: Via SFTP or Samba share
```

### Public SaaS (Many users)
✅ **Per-user upload** + database isolation
```
Backend: Cloud server
Folder: /app/uploads/{user_id}/
Upload: Via web upload interface
Storage: S3 or similar
```

### Enterprise
✅ **Cloud storage integration**
```
Backend: Kubernetes cluster
Folder: S3/GCS bucket mounted as filesystem
Upload: API + Admin tools
Search: Multi-tenant with isolation
```

---

## Adding Upload Feature

Want users to upload PDFs instead of configuring folders? I can add:

### Frontend Changes:
1. Upload page with drag & drop
2. Progress tracking
3. File list management

### Backend Changes:
1. Upload endpoint (`POST /api/v1/documents/upload`)
2. Multi-file support
3. Auto-trigger ingestion

Would you like me to implement this? It would work great for:
- Mobile users
- Remote deployments (Vercel + Supabase)
- Multi-user scenarios

---

## Quick Decision Guide

**Question: Where will your backend run?**

| Backend Location | Folder Access | Best Solution |
|-----------------|---------------|---------------|
| My laptop | ✅ Local folders | Current approach ✓ |
| My home server | ✅ Server folders | SFTP + current approach |
| Cloud (Vercel functions) | ❌ No filesystem | Add upload API |
| Supabase | ✅ Server folders | Server folders + upload |
| Cloud (AWS/GCP) | ✅ With mount | S3 mount + upload API |

**For Vercel + Supabase:**
- Backend on Supabase (has filesystem)
- Create `/app/pdfs` folder on Supabase
- Upload PDFs to Supabase server (SFTP/API)
- Use folder path `/app/pdfs`

Let me know if you want me to add the upload feature! 🚀


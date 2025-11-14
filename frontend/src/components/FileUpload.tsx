/**
 * FileUpload component
 * Allows users to upload PDF files directly for processing.
 */
import { useState, useRef } from 'react';
import { uploadPDF, getDocumentStatus, UploadResponse } from '../api';

interface UploadedFile {
  file: File;
  response?: UploadResponse;
  status: 'pending' | 'uploading' | 'processing' | 'done' | 'error';
  error?: string;
  progress?: string;
}

export default function FileUpload() {
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFiles = (fileList: FileList | null) => {
    if (!fileList) return;

    const pdfFiles = Array.from(fileList).filter(file => 
      file.name.toLowerCase().endsWith('.pdf')
    );

    if (pdfFiles.length === 0) {
      alert('Please select PDF files only');
      return;
    }

    const newFiles: UploadedFile[] = pdfFiles.map(file => ({
      file,
      status: 'pending'
    }));

    setFiles(prev => [...prev, ...newFiles]);

    // Start uploading
    newFiles.forEach((fileObj, index) => {
      uploadFile(fileObj, files.length + index);
    });
  };

  const uploadFile = async (fileObj: UploadedFile, index: number) => {
    try {
      // Update status to uploading
      setFiles(prev => {
        const updated = [...prev];
        updated[index] = { ...updated[index], status: 'uploading', progress: 'Uploading...' };
        return updated;
      });

      // Upload file
      const response = await uploadPDF(fileObj.file);

      // Update with response
      setFiles(prev => {
        const updated = [...prev];
        updated[index] = {
          ...updated[index],
          response,
          status: 'processing',
          progress: 'Processing...'
        };
        return updated;
      });

      // Poll for status
      pollDocumentStatus(response.document_id, index);

    } catch (error) {
      setFiles(prev => {
        const updated = [...prev];
        updated[index] = {
          ...updated[index],
          status: 'error',
          error: `Upload failed: ${error}`
        };
        return updated;
      });
    }
  };

  const pollDocumentStatus = async (documentId: number, index: number) => {
    let attempts = 0;
    const maxAttempts = 60; // 2 minutes

    const poll = setInterval(async () => {
      try {
        attempts++;
        const status = await getDocumentStatus(documentId);

        if (status.status === 'done') {
          clearInterval(poll);
          setFiles(prev => {
            const updated = [...prev];
            updated[index] = {
              ...updated[index],
              status: 'done',
              progress: `✅ Complete! ${status.page_count || 0} pages processed`
            };
            return updated;
          });
        } else if (status.status === 'error') {
          clearInterval(poll);
          setFiles(prev => {
            const updated = [...prev];
            updated[index] = {
              ...updated[index],
              status: 'error',
              error: status.error_message || 'Processing failed'
            };
            return updated;
          });
        } else {
          // Still processing
          setFiles(prev => {
            const updated = [...prev];
            updated[index] = {
              ...updated[index],
              progress: `⏳ Processing... (${attempts}s)`
            };
            return updated;
          });
        }

        if (attempts >= maxAttempts) {
          clearInterval(poll);
          setFiles(prev => {
            const updated = [...prev];
            updated[index] = {
              ...updated[index],
              status: 'error',
              error: 'Processing timeout'
            };
            return updated;
          });
        }
      } catch (error) {
        console.error('Failed to check status:', error);
      }
    }, 2000);
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files) {
      handleFiles(e.dataTransfer.files);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files) {
      handleFiles(e.target.files);
    }
  };

  const handleButtonClick = () => {
    fileInputRef.current?.click();
  };

  const clearFiles = () => {
    setFiles([]);
  };

  return (
    <div style={{ padding: '20px', maxWidth: '600px', borderBottom: '1px solid #ddd' }}>
      <h3>📤 Upload PDF Files</h3>
      <p style={{ fontSize: '14px', color: '#666', marginBottom: '15px' }}>
        Upload PDF files directly for immediate processing
      </p>

      {/* Drop zone */}
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        style={{
          border: dragActive ? '2px dashed #007bff' : '2px dashed #ddd',
          borderRadius: '8px',
          padding: '40px 20px',
          textAlign: 'center',
          backgroundColor: dragActive ? '#f0f8ff' : '#f9f9f9',
          cursor: 'pointer',
          marginBottom: '20px',
          transition: 'all 0.3s ease'
        }}
        onClick={handleButtonClick}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".pdf"
          onChange={handleChange}
          style={{ display: 'none' }}
        />
        
        <div style={{ fontSize: '48px', marginBottom: '10px' }}>📁</div>
        <p style={{ margin: '10px 0', fontSize: '16px', fontWeight: 'bold' }}>
          {dragActive ? 'Drop files here' : 'Drag & drop PDF files here'}
        </p>
        <p style={{ margin: '5px 0', fontSize: '14px', color: '#666' }}>
          or click to browse
        </p>
        <button
          onClick={(e) => {
            e.stopPropagation();
            handleButtonClick();
          }}
          style={{
            marginTop: '15px',
            padding: '10px 20px',
            fontSize: '14px',
            cursor: 'pointer',
            backgroundColor: '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '4px'
          }}
        >
          📎 Select PDF Files
        </button>
      </div>

      {/* File list */}
      {files.length > 0 && (
        <>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
            <h4 style={{ margin: 0 }}>Uploaded Files ({files.length})</h4>
            <button
              onClick={clearFiles}
              style={{
                padding: '5px 10px',
                fontSize: '12px',
                cursor: 'pointer',
                backgroundColor: '#6c757d',
                color: 'white',
                border: 'none',
                borderRadius: '4px'
              }}
            >
              Clear All
            </button>
          </div>

          <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
            {files.map((fileObj, index) => (
              <div
                key={index}
                style={{
                  padding: '12px',
                  marginBottom: '10px',
                  backgroundColor: '#fff',
                  border: '1px solid #ddd',
                  borderRadius: '4px',
                  borderLeft: `4px solid ${
                    fileObj.status === 'done' ? '#28a745' :
                    fileObj.status === 'error' ? '#dc3545' :
                    fileObj.status === 'uploading' ? '#ffc107' :
                    '#007bff'
                  }`
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: 'bold', fontSize: '14px', marginBottom: '4px' }}>
                      {fileObj.file.name}
                    </div>
                    <div style={{ fontSize: '12px', color: '#666' }}>
                      {(fileObj.file.size / 1024 / 1024).toFixed(2)} MB
                    </div>
                    {fileObj.progress && (
                      <div style={{ fontSize: '13px', marginTop: '6px', color: '#007bff' }}>
                        {fileObj.progress}
                      </div>
                    )}
                    {fileObj.error && (
                      <div style={{ fontSize: '13px', marginTop: '6px', color: '#dc3545' }}>
                        ❌ {fileObj.error}
                      </div>
                    )}
                    {fileObj.response && (
                      <div style={{ fontSize: '12px', marginTop: '6px', color: '#666' }}>
                        Document ID: {fileObj.response.document_id}
                      </div>
                    )}
                  </div>
                  <div style={{
                    fontSize: '24px',
                    marginLeft: '10px'
                  }}>
                    {fileObj.status === 'done' && '✅'}
                    {fileObj.status === 'error' && '❌'}
                    {fileObj.status === 'uploading' && '⬆️'}
                    {fileObj.status === 'processing' && '⚙️'}
                    {fileObj.status === 'pending' && '⏳'}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      {/* Tips */}
      <details style={{ marginTop: '15px', fontSize: '12px', color: '#666' }}>
        <summary style={{ cursor: 'pointer', fontWeight: 'bold' }}>
          💡 Upload Tips
        </summary>
        <div style={{ marginTop: '8px', paddingLeft: '12px' }}>
          <ul style={{ margin: '4px 0 0 20px' }}>
            <li>Upload multiple files at once</li>
            <li>Files are processed immediately</li>
            <li>Processing takes ~5-10 seconds per page</li>
            <li>Once done, files are searchable instantly</li>
            <li>Duplicate files (same content) are automatically detected</li>
          </ul>
        </div>
      </details>
    </div>
  );
}


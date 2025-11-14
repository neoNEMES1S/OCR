"""
Unit tests for scanner module.
Tests file discovery, checksum computation, and idempotent scanning.
"""
import pytest
from pathlib import Path
from datetime import datetime
from app.workers.scanner import scan_folder, should_ingest_file, _get_file_info


@pytest.fixture
def temp_pdf_dir(tmp_path):
    """
    Create a temporary directory with test PDF files.
    
    Creates:
    - file1.pdf (simple PDF)
    - file2.pdf (another PDF)
    - subdir/file3.pdf (nested PDF)
    - not_a_pdf.txt (non-PDF file)
    """
    # Create some dummy PDF-like files for testing
    pdf1 = tmp_path / "file1.pdf"
    pdf1.write_text("%PDF-1.4\nTest PDF content for file 1")
    
    pdf2 = tmp_path / "file2.pdf"
    pdf2.write_text("%PDF-1.4\nTest PDF content for file 2")
    
    # Create subdirectory with a PDF
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    pdf3 = subdir / "file3.pdf"
    pdf3.write_text("%PDF-1.4\nTest PDF content for file 3")
    
    # Create a non-PDF file (should be ignored)
    txt_file = tmp_path / "not_a_pdf.txt"
    txt_file.write_text("This is not a PDF")
    
    return tmp_path


def test_scan_folder_finds_pdfs(temp_pdf_dir):
    """Test that scanner finds PDF files in directory."""
    results = scan_folder(str(temp_pdf_dir), include_subfolders=False)
    
    # Should find 2 PDFs (file1.pdf, file2.pdf), not the subdirectory one
    assert len(results) == 2
    
    filenames = [r['filename'] for r in results]
    assert 'file1.pdf' in filenames
    assert 'file2.pdf' in filenames
    assert 'file3.pdf' not in filenames  # In subdirectory
    assert 'not_a_pdf.txt' not in filenames  # Not a PDF


def test_scan_folder_with_subfolders(temp_pdf_dir):
    """Test that scanner finds PDFs recursively when include_subfolders=True."""
    results = scan_folder(str(temp_pdf_dir), include_subfolders=True)
    
    # Should find all 3 PDFs
    assert len(results) == 3
    
    filenames = [r['filename'] for r in results]
    assert 'file1.pdf' in filenames
    assert 'file2.pdf' in filenames
    assert 'file3.pdf' in filenames


def test_scan_folder_returns_metadata(temp_pdf_dir):
    """Test that scanner returns correct metadata for files."""
    results = scan_folder(str(temp_pdf_dir), include_subfolders=False)
    
    assert len(results) > 0
    
    result = results[0]
    
    # Check required fields
    assert 'path' in result
    assert 'filename' in result
    assert 'sha256' in result
    assert 'last_modified' in result
    assert 'file_size' in result
    
    # Check types
    assert isinstance(result['path'], str)
    assert isinstance(result['filename'], str)
    assert isinstance(result['sha256'], str)
    assert isinstance(result['last_modified'], datetime)
    assert isinstance(result['file_size'], int)
    
    # SHA256 should be 64 hex characters
    assert len(result['sha256']) == 64
    assert all(c in '0123456789abcdef' for c in result['sha256'])


def test_scan_folder_checksum_changes(temp_pdf_dir):
    """Test that changing file content changes checksum."""
    # First scan
    results1 = scan_folder(str(temp_pdf_dir), include_subfolders=False)
    file1_result = [r for r in results1 if r['filename'] == 'file1.pdf'][0]
    original_checksum = file1_result['sha256']
    
    # Modify file
    pdf1 = temp_pdf_dir / "file1.pdf"
    pdf1.write_text("%PDF-1.4\nModified content - different now!")
    
    # Second scan
    results2 = scan_folder(str(temp_pdf_dir), include_subfolders=False)
    file1_result_new = [r for r in results2 if r['filename'] == 'file1.pdf'][0]
    new_checksum = file1_result_new['sha256']
    
    # Checksums should be different
    assert original_checksum != new_checksum


def test_scan_folder_nonexistent_path():
    """Test that scanner raises error for nonexistent path."""
    with pytest.raises(FileNotFoundError):
        scan_folder("/path/that/does/not/exist")


def test_scan_folder_file_instead_of_directory(temp_pdf_dir):
    """Test that scanner raises error when given a file instead of directory."""
    pdf_file = temp_pdf_dir / "file1.pdf"
    
    with pytest.raises(NotADirectoryError):
        scan_folder(str(pdf_file))


def test_should_ingest_file_new_file():
    """Test that new files should be ingested."""
    result = should_ingest_file(
        existing_checksum=None,
        existing_modified=None,
        new_checksum="abc123",
        new_modified=datetime.now()
    )
    assert result is True


def test_should_ingest_file_changed_content():
    """Test that files with changed content should be re-ingested."""
    result = should_ingest_file(
        existing_checksum="old_checksum",
        existing_modified=datetime(2024, 1, 1),
        new_checksum="new_checksum",
        new_modified=datetime(2024, 1, 2)
    )
    assert result is True


def test_should_ingest_file_unchanged():
    """Test that unchanged files should not be re-ingested."""
    checksum = "same_checksum"
    modified = datetime(2024, 1, 1)
    
    result = should_ingest_file(
        existing_checksum=checksum,
        existing_modified=modified,
        new_checksum=checksum,
        new_modified=modified
    )
    assert result is False


def test_get_file_info(temp_pdf_dir):
    """Test file info extraction."""
    pdf_file = temp_pdf_dir / "file1.pdf"
    info = _get_file_info(pdf_file)
    
    assert info['filename'] == 'file1.pdf'
    assert info['path'] == str(pdf_file.absolute())
    assert len(info['sha256']) == 64
    assert info['file_size'] > 0
    assert isinstance(info['last_modified'], datetime)

"""
Integration tests for scan API endpoint.
Tests scan job creation and RQ queue integration.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import create_app
from app.db import get_db_dependency
from app.models import Base


# Test database setup
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture
def test_db():
    """Create a test database."""
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    yield TestingSessionLocal
    
    # Cleanup
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(test_db):
    """Create a test client with database override."""
    app = create_app()
    
    # Override database dependency
    def override_get_db():
        db = test_db()
        try:
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db_dependency] = override_get_db
    
    with TestClient(app) as c:
        yield c


@pytest.fixture
def temp_pdf_dir(tmp_path):
    """Create temporary directory with a test PDF."""
    pdf = tmp_path / "test.pdf"
    pdf.write_text("%PDF-1.4\nTest PDF content")
    return tmp_path


@patch('app.api.v1.scan.get_queue')
def test_trigger_scan_creates_job(mock_get_queue, client, temp_pdf_dir):
    """Test that POST /api/v1/scan creates a scan job and enqueues work."""
    # Mock RQ queue
    mock_queue = Mock()
    mock_rq_job = Mock()
    mock_rq_job.id = "rq-job-123"
    mock_queue.enqueue.return_value = mock_rq_job
    mock_get_queue.return_value = mock_queue
    
    # Trigger scan
    response = client.post(
        "/api/v1/scan",
        json={
            "path": str(temp_pdf_dir),
            "include_subfolders": False
        }
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    
    assert 'job_id' in data
    assert data['scan_path'] == str(temp_pdf_dir)
    assert data['include_subfolders'] is False
    assert 'message' in data
    
    # Check that queue.enqueue was called
    mock_queue.enqueue.assert_called_once()
    call_args = mock_queue.enqueue.call_args
    
    # Verify function name
    assert call_args[0][0] == 'app.workers.ingest_worker.scan_and_ingest_job'
    
    # Verify arguments (path, include_subfolders, job_id)
    assert call_args[0][1] == str(temp_pdf_dir)
    assert call_args[0][2] is False


@patch('app.api.v1.scan.get_queue')
def test_trigger_scan_uses_default_settings(mock_get_queue, client):
    """Test that scan uses default settings when no parameters provided."""
    # Mock RQ queue
    mock_queue = Mock()
    mock_rq_job = Mock()
    mock_rq_job.id = "rq-job-456"
    mock_queue.enqueue.return_value = mock_rq_job
    mock_get_queue.return_value = mock_queue
    
    # Trigger scan without parameters
    response = client.post("/api/v1/scan", json={})
    
    # Should succeed and use config defaults
    assert response.status_code == 200
    data = response.json()
    
    assert 'job_id' in data
    assert 'scan_path' in data  # Should have used config default


def test_get_scan_status_not_found(client):
    """Test that GET /api/v1/scan/{job_id} returns 404 for nonexistent job."""
    response = client.get("/api/v1/scan/nonexistent-job-id")
    
    assert response.status_code == 404
    assert "not found" in response.json()['detail'].lower()


@patch('app.api.v1.scan.get_queue')
def test_get_scan_status_returns_job_info(mock_get_queue, client, temp_pdf_dir):
    """Test that GET /api/v1/scan/{job_id} returns scan job status."""
    # Mock RQ queue
    mock_queue = Mock()
    mock_rq_job = Mock()
    mock_rq_job.id = "rq-job-789"
    mock_queue.enqueue.return_value = mock_rq_job
    mock_get_queue.return_value = mock_queue
    
    # Create scan job
    create_response = client.post(
        "/api/v1/scan",
        json={"path": str(temp_pdf_dir), "include_subfolders": True}
    )
    job_id = create_response.json()['job_id']
    
    # Get status
    status_response = client.get(f"/api/v1/scan/{job_id}")
    
    assert status_response.status_code == 200
    data = status_response.json()
    
    assert data['job_id'] == job_id
    assert data['scan_path'] == str(temp_pdf_dir)
    assert data['include_subfolders'] is True
    assert data['status'] == 'running'
    assert 'started_at' in data


def test_health_endpoint(client):
    """Test that health check endpoint works."""
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data['status'] == 'healthy'


def test_root_endpoint(client):
    """Test that root endpoint returns API info."""
    response = client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    
    assert 'message' in data
    assert 'endpoints' in data

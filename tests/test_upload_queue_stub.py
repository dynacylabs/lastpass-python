"""Tests for upload queue module."""
import pytest
from unittest.mock import Mock, patch, mock_open
import json
import os
from pathlib import Path

from lastpass.upload_queue import UploadQueue


@pytest.fixture
def temp_config(tmp_path):
    """Create temporary config."""
    from lastpass.config import Config
    config_dir = tmp_path / "lpass"
    config_dir.mkdir()
    config = Config()
    config.config_dir = config_dir
    return config


@pytest.fixture
def upload_queue(temp_config):
    """Create UploadQueue with temporary config."""
    return UploadQueue(temp_config)


@pytest.mark.unit
class TestUploadQueueInit:
    """Tests for UploadQueue initialization."""
    
    def test_init_default_config(self):
        """Test initialization with default config."""
        queue = UploadQueue()
        assert queue.config is not None
        assert queue._queue_dir is not None
    
    def test_init_custom_config(self, temp_config):
        """Test initialization with custom config."""
        queue = UploadQueue(temp_config)
        assert queue.config == temp_config
    
    def test_get_queue_dir(self, upload_queue):
        """Test getting queue directory."""
        queue_dir = upload_queue._get_queue_dir()
        assert queue_dir is not None
        assert isinstance(queue_dir, Path)


@pytest.mark.unit
class TestUploadQueueEnqueue:
    """Tests for enqueue method."""
    
    def test_enqueue_creates_entry(self, upload_queue):
        """Test enqueue creates queue entry."""
        endpoint = '/api/test'
        params = {'param1': 'value1'}
        key = b'0' * 32
        
        # Should not raise exception
        upload_queue.enqueue(endpoint, params, key)
        
        # Check queue directory was created
        assert upload_queue._queue_dir.exists()


@pytest.mark.unit
class TestUploadQueueBasic:
    """Basic tests for UploadQueue methods."""
    
    def test_ensure_dirs(self, upload_queue):
        """Test directory creation."""
        upload_queue._ensure_dirs()
        assert upload_queue._queue_dir.exists()
        assert upload_queue._lock_dir.exists()
        assert upload_queue._fail_dir.exists()

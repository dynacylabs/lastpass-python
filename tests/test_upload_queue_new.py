"""Tests for upload_queue module."""
import pytest
from unittest.mock import Mock, patch, MagicMock, mock_open
import os
import time
import json
from pathlib import Path

from lastpass.upload_queue import UploadQueue
from lastpass.config import Config


@pytest.fixture
def temp_config(tmp_path):
    """Create temporary config."""
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
    
    def test_init_custom_config(self, temp_config):
        """Test initialization with custom config."""
        queue = UploadQueue(temp_config)
        assert queue.config == temp_config
    
    def test_queue_directories(self, upload_queue):
        """Test queue directory structure."""
        assert upload_queue._queue_dir.name == 'upload-queue'
        assert upload_queue._lock_dir.name == 'locks'
        assert upload_queue._fail_dir.name == 'failed'


@pytest.mark.unit
class TestEnqueue:
    """Tests for enqueue method."""
    
    @patch('lastpass.upload_queue.encrypt_aes256_cbc_base64')
    @patch('time.time')
    def test_enqueue_basic(self, mock_time, mock_encrypt, upload_queue):
        """Test basic enqueue operation."""
        mock_time.return_value = 1234567890.0
        mock_encrypt.return_value = 'encrypted_data'
        key = b'0' * 32
        
        upload_queue.enqueue('/api/endpoint', {'param': 'value'}, key)
        
        # Check that file was created (exclude directories)
        queue_files = [f for f in upload_queue._queue_dir.glob('*') if f.is_file()]
        assert len(queue_files) == 1
        
        # Check file content
        content = queue_files[0].read_text()
        assert content == 'encrypted_data'
    
    @patch('lastpass.upload_queue.encrypt_aes256_cbc_base64')
    @patch('time.time')
    def test_enqueue_creates_directories(self, mock_time, mock_encrypt, temp_config):
        """Test enqueue creates necessary directories."""
        mock_time.return_value = 1234567890.0
        mock_encrypt.return_value = 'encrypted_data'
        key = b'0' * 32
        
        queue = UploadQueue(temp_config)
        queue.enqueue('/api/test', {}, key)
        
        assert queue._queue_dir.exists()
        assert queue._lock_dir.exists()
        assert queue._fail_dir.exists()
    
    @patch('lastpass.upload_queue.encrypt_aes256_cbc_base64')
    @patch('time.time')
    def test_enqueue_unique_filenames(self, mock_time, mock_encrypt, upload_queue):
        """Test enqueue creates unique filenames."""
        mock_time.return_value = 1234567890.0
        mock_encrypt.return_value = 'data'
        key = b'0' * 32
        
        upload_queue.enqueue('/api/1', {}, key)
        upload_queue.enqueue('/api/2', {}, key)
        upload_queue.enqueue('/api/3', {}, key)
        
        queue_files = [f for f in upload_queue._queue_dir.glob('*') if f.is_file()]
        assert len(queue_files) == 3
        
        # All filenames should be unique
        filenames = [f.name for f in queue_files]
        assert len(set(filenames)) == 3
    
    @patch('lastpass.upload_queue.encrypt_aes256_cbc_base64')
    @patch('time.time')
    def test_enqueue_serializes_correctly(self, mock_time, mock_encrypt, upload_queue):
        """Test enqueue serializes data correctly."""
        mock_time.return_value = 1234567890.0
        key = b'0' * 32
        
        endpoint = '/api/update'
        params = {'id': '123', 'name': 'test'}
        
        def encrypt_side_effect(data, k):
            # Verify JSON structure
            entry = json.loads(data)
            assert entry['endpoint'] == endpoint
            assert entry['params'] == params
            assert 'timestamp' in entry
            return 'encrypted'
        
        mock_encrypt.side_effect = encrypt_side_effect
        upload_queue.enqueue(endpoint, params, key)
    
    @patch('lastpass.upload_queue.encrypt_aes256_cbc_base64')
    @patch('time.time')
    def test_enqueue_no_slots_available(self, mock_time, mock_encrypt, upload_queue):
        """Test enqueue raises error when no slots available."""
        mock_time.return_value = 1234567890.0
        mock_encrypt.return_value = 'data'
        key = b'0' * 32
        
        # Create 10000 dummy files to exhaust slots
        with patch.object(Path, 'exists', return_value=True):
            with pytest.raises(RuntimeError, match="No available upload queue slots"):
                upload_queue.enqueue('/api/test', {}, key)


@pytest.mark.unit
class TestGetNextEntry:
    """Tests for _get_next_entry method."""
    
    @patch('lastpass.upload_queue.decrypt_aes256_cbc_base64')
    def test_get_next_entry_success(self, mock_decrypt, upload_queue):
        """Test getting next entry."""
        key = b'0' * 32
        
        # Create a queue entry
        entry = {'endpoint': '/api/test', 'params': {}, 'timestamp': time.time()}
        entry_json = json.dumps(entry)
        mock_decrypt.return_value = entry_json
        
        queue_file = upload_queue._queue_dir / '1234567890'
        upload_queue._queue_dir.mkdir(parents=True, exist_ok=True)
        queue_file.write_text('encrypted_data')
        
        result = upload_queue._get_next_entry(key)
        
        assert result is not None
        filename, returned_entry, lock_file = result
        assert filename == '1234567890'
        assert returned_entry['endpoint'] == '/api/test'
        assert lock_file.exists()
    
    def test_get_next_entry_empty_queue(self, upload_queue):
        """Test getting next entry from empty queue."""
        key = b'0' * 32
        result = upload_queue._get_next_entry(key)
        assert result is None
    
    @patch('lastpass.upload_queue.decrypt_aes256_cbc_base64')
    def test_get_next_entry_skips_locked(self, mock_decrypt, upload_queue):
        """Test skips locked entries."""
        key = b'0' * 32
        upload_queue._ensure_dirs()
        
        # Create two queue entries
        entry = {'endpoint': '/api/test', 'params': {}, 'timestamp': time.time()}
        entry_json = json.dumps(entry)
        mock_decrypt.return_value = entry_json
        
        file1 = upload_queue._queue_dir / '0001'
        file2 = upload_queue._queue_dir / '0002'
        file1.write_text('encrypted')
        file2.write_text('encrypted')
        
        # Lock first file
        lock1 = upload_queue._lock_dir / '0001'
        lock1.touch()
        
        result = upload_queue._get_next_entry(key)
        
        # Should get second file
        assert result is not None
        filename, _, _ = result
        assert filename == '0002'
    
    @patch('lastpass.upload_queue.decrypt_aes256_cbc_base64')
    def test_get_next_entry_decrypt_error(self, mock_decrypt, upload_queue):
        """Test handles decrypt errors."""
        key = b'0' * 32
        upload_queue._ensure_dirs()
        
        file1 = upload_queue._queue_dir / '0001'
        file1.write_text('bad_data')
        mock_decrypt.side_effect = Exception("Decrypt failed")
        
        result = upload_queue._get_next_entry(key)
        
        # Should return None and not raise
        assert result is None
    
    @patch('lastpass.upload_queue.decrypt_aes256_cbc_base64')
    def test_get_next_entry_sorted(self, mock_decrypt, upload_queue):
        """Test entries processed in order."""
        key = b'0' * 32
        upload_queue._ensure_dirs()
        
        entry = {'endpoint': '/api/test', 'params': {}, 'timestamp': time.time()}
        entry_json = json.dumps(entry)
        mock_decrypt.return_value = entry_json
        
        # Create files in random order
        (upload_queue._queue_dir / '0003').write_text('enc')
        (upload_queue._queue_dir / '0001').write_text('enc')
        (upload_queue._queue_dir / '0002').write_text('enc')
        
        result = upload_queue._get_next_entry(key)
        
        # Should get first file (sorted)
        filename, _, _ = result
        assert filename == '0001'


@pytest.mark.unit
class TestDropEntry:
    """Tests for _drop_entry method."""
    
    def test_drop_entry_removes_files(self, upload_queue):
        """Test drop entry removes files."""
        upload_queue._ensure_dirs()
        
        queue_file = upload_queue._queue_dir / '0001'
        lock_file = upload_queue._lock_dir / '0001'
        queue_file.touch()
        lock_file.touch()
        
        upload_queue._drop_entry('0001')
        
        assert not queue_file.exists()
        assert not lock_file.exists()
    
    def test_drop_entry_missing_files(self, upload_queue):
        """Test drop entry with missing files."""
        # Should not raise exception
        upload_queue._drop_entry('nonexistent')


@pytest.mark.unit
class TestMarkFailed:
    """Tests for _mark_failed method."""
    
    def test_mark_failed_moves_to_fail_dir(self, upload_queue):
        """Test mark failed moves file to fail directory."""
        upload_queue._ensure_dirs()
        
        queue_file = upload_queue._queue_dir / '0001'
        lock_file = upload_queue._lock_dir / '0001'
        queue_file.write_text('data')
        lock_file.touch()
        
        upload_queue._mark_failed('0001')
        
        assert not queue_file.exists()
        assert not lock_file.exists()
        assert (upload_queue._fail_dir / '0001').exists()
    
    def test_mark_failed_missing_file(self, upload_queue):
        """Test mark failed with missing file."""
        upload_queue._ensure_dirs()
        
        # Should not raise exception
        upload_queue._mark_failed('nonexistent')


@pytest.mark.unit
class TestCleanupFailures:
    """Tests for _cleanup_failures method."""
    
    def test_cleanup_failures_removes_old(self, upload_queue):
        """Test cleanup removes old failed entries."""
        upload_queue._ensure_dirs()
        
        fail_file = upload_queue._fail_dir / 'old_entry'
        fail_file.touch()
        
        # Set modification time to 15 days ago
        old_time = time.time() - (15 * 24 * 60 * 60)
        os.utime(fail_file, (old_time, old_time))
        
        upload_queue._cleanup_failures()
        
        assert not fail_file.exists()
    
    def test_cleanup_failures_keeps_recent(self, upload_queue):
        """Test cleanup keeps recent failed entries."""
        upload_queue._ensure_dirs()
        
        fail_file = upload_queue._fail_dir / 'recent_entry'
        fail_file.touch()
        
        upload_queue._cleanup_failures()
        
        assert fail_file.exists()


@pytest.mark.unit
class TestIsRunning:
    """Tests for is_running method."""
    
    def test_is_running_no_pid_file(self, upload_queue):
        """Test is_running when no PID file."""
        assert upload_queue.is_running() is False
    
    @patch('os.kill')
    def test_is_running_process_exists(self, mock_kill, upload_queue):
        """Test is_running when process exists."""
        upload_queue._ensure_dirs()
        
        pid_file = upload_queue._queue_dir / 'processor.pid'
        pid_file.write_text('12345')
        
        # Process exists
        mock_kill.return_value = None
        
        assert upload_queue.is_running() is True
        mock_kill.assert_called_with(12345, 0)
    
    @patch('os.kill')
    def test_is_running_process_not_exists(self, mock_kill, upload_queue):
        """Test is_running when process doesn't exist."""
        upload_queue._ensure_dirs()
        
        pid_file = upload_queue._queue_dir / 'processor.pid'
        pid_file.write_text('12345')
        
        # Process doesn't exist
        mock_kill.side_effect = OSError()
        
        assert upload_queue.is_running() is False
        # PID file should be cleaned up
        assert not pid_file.exists()
    
    def test_is_running_invalid_pid(self, upload_queue):
        """Test is_running with invalid PID."""
        upload_queue._ensure_dirs()
        
        pid_file = upload_queue._queue_dir / 'processor.pid'
        pid_file.write_text('not_a_number')
        
        assert upload_queue.is_running() is False


@pytest.mark.unit
class TestKill:
    """Tests for kill method."""
    
    @patch('os.kill')
    @patch('time.sleep')
    def test_kill_terminates_process(self, mock_sleep, mock_kill, upload_queue):
        """Test kill terminates processor."""
        upload_queue._ensure_dirs()
        
        pid_file = upload_queue._queue_dir / 'processor.pid'
        pid_file.write_text('12345')
        
        upload_queue.kill()
        
        import signal
        mock_kill.assert_called_with(12345, signal.SIGTERM)
        assert not pid_file.exists()
    
    def test_kill_no_pid_file(self, upload_queue):
        """Test kill when no PID file."""
        # Should not raise exception
        upload_queue.kill()
    
    @patch('os.kill')
    def test_kill_process_not_found(self, mock_kill, upload_queue):
        """Test kill when process not found."""
        upload_queue._ensure_dirs()
        
        pid_file = upload_queue._queue_dir / 'processor.pid'
        pid_file.write_text('12345')
        
        mock_kill.side_effect = OSError()
        
        # Should not raise exception
        upload_queue.kill()


@pytest.mark.unit
class TestUploadAll:
    """Tests for upload_all method."""
    
    @patch.object(UploadQueue, '_cleanup_failures')
    @patch.object(UploadQueue, '_get_next_entry')
    def test_upload_all_empty_queue(self, mock_get_next, mock_cleanup, upload_queue):
        """Test upload_all with empty queue."""
        mock_get_next.return_value = None
        session = Mock()
        key = b'0' * 32
        
        upload_queue.upload_all(session, key)
        
        mock_cleanup.assert_called_once()
        mock_get_next.assert_called_once()
    
    @patch('lastpass.http.HTTPClient')
    @patch.object(UploadQueue, '_cleanup_failures')
    @patch.object(UploadQueue, '_get_next_entry')
    @patch.object(UploadQueue, '_drop_entry')
    def test_upload_all_success(self, mock_drop, mock_get_next, mock_cleanup, mock_http_cls, upload_queue):
        """Test upload_all with successful upload."""
        # Setup mocks
        session = Mock()
        session.server = 'lastpass.com'
        key = b'0' * 32
        
        entry = {'endpoint': '/api/test', 'params': {'key': 'value'}, 'timestamp': time.time()}
        lock_file = Mock()
        
        mock_get_next.side_effect = [
            ('0001', entry, lock_file),
            None  # End iteration
        ]
        
        mock_http = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_http.post.return_value = mock_response
        mock_http_cls.return_value = mock_http
        
        upload_queue.upload_all(session, key)
        
        # Should have dropped entry
        mock_drop.assert_called_with('0001')
        lock_file.unlink.assert_called()
    
    @patch('lastpass.http.HTTPClient')
    @patch('time.sleep')
    @patch.object(UploadQueue, '_cleanup_failures')
    @patch.object(UploadQueue, '_get_next_entry')
    @patch.object(UploadQueue, '_mark_failed')
    def test_upload_all_retry_on_error(self, mock_mark_failed, mock_get_next, mock_cleanup, mock_sleep, mock_http_cls, upload_queue):
        """Test upload_all retries on error."""
        session = Mock()
        session.server = 'lastpass.com'
        key = b'0' * 32
        
        entry = {'endpoint': '/api/test', 'params': {}, 'timestamp': time.time()}
        lock_file = Mock()
        
        mock_get_next.side_effect = [
            ('0001', entry, lock_file),
            None
        ]
        
        mock_http = Mock()
        mock_http.post.side_effect = Exception("Network error")
        mock_http_cls.return_value = mock_http
        
        upload_queue.upload_all(session, key)
        
        # Should have marked as failed after retries
        mock_mark_failed.assert_called_with('0001')
        # Should have retried multiple times
        assert mock_http.post.call_count == UploadQueue.MAX_RETRIES

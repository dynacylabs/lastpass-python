"""Tests for editor integration."""
import pytest
from unittest.mock import Mock, patch, mock_open, MagicMock
import tempfile
import os
import subprocess
from pathlib import Path

from lastpass.editor import Editor
from lastpass.models import Account, Field


@pytest.mark.unit
class TestGetEditor:
    """Tests for getting editor."""
    
    @patch.dict(os.environ, {'EDITOR': 'vim'})
    def test_get_editor_from_editor_env(self):
        """Test getting editor from EDITOR env var."""
        editor = Editor._get_editor()
        assert editor == 'vim'
    
    @patch.dict(os.environ, {'VISUAL': 'emacs'}, clear=True)
    def test_get_editor_from_visual_env(self):
        """Test getting editor from VISUAL env var."""
        editor = Editor._get_editor()
        assert editor == 'emacs'
    
    @patch.dict(os.environ, {}, clear=True)
    @patch('subprocess.run')
    def test_get_editor_default_vi(self, mock_run):
        """Test getting default editor (vi)."""
        mock_run.return_value = Mock(returncode=0)
        editor = Editor._get_editor()
        assert editor in ['vi', 'vim', 'nano', 'emacs']
    
    @patch.dict(os.environ, {}, clear=True)
    @patch('subprocess.run')
    def test_get_editor_fallback_to_vi(self, mock_run):
        """Test fallback to vi when no editors found."""
        mock_run.return_value = Mock(returncode=1)
        editor = Editor._get_editor()
        assert editor == 'vi'


@pytest.mark.unit
class TestGetSecureTmpdir:
    """Tests for getting secure temporary directory."""
    
    @patch.dict(os.environ, {'SECURE_TMPDIR': '/secure/tmp'})
    def test_get_secure_tmpdir_from_env(self):
        """Test getting secure tmpdir from environment."""
        with patch('pathlib.Path.exists', return_value=True):
            tmpdir = Editor._get_secure_tmpdir()
            assert str(tmpdir) == '/secure/tmp'
    
    @patch.dict(os.environ, {'TMPDIR': '/custom/tmp'}, clear=True)
    def test_get_secure_tmpdir_from_tmpdir(self):
        """Test getting tmpdir from TMPDIR env var."""
        tmpdir = Editor._get_secure_tmpdir()
        assert str(tmpdir) == '/custom/tmp'
    
    @patch.dict(os.environ, {}, clear=True)
    def test_get_secure_tmpdir_default(self):
        """Test getting default tmpdir."""
        tmpdir = Editor._get_secure_tmpdir()
        assert str(tmpdir) == '/tmp'


@pytest.mark.unit
class TestEditText:
    """Tests for edit_text function."""
    
    @patch('tempfile.mkstemp')
    @patch('subprocess.run')
    @patch.object(Editor, '_get_editor')
    @patch.object(Editor, '_get_secure_tmpdir')
    @patch('os.chmod')
    @patch('os.unlink')
    def test_edit_text_success(self, mock_unlink, mock_chmod, mock_tmpdir, 
                               mock_get_editor, mock_subprocess, mock_mkstemp):
        """Test successful text editing."""
        # Setup
        mock_fd = 3
        mock_tmpfile = '/tmp/lpass-test.txt'
        mock_mkstemp.return_value = (mock_fd, mock_tmpfile)
        mock_get_editor.return_value = 'vim'
        mock_tmpdir.return_value = Path('/tmp')
        mock_subprocess.return_value = Mock(returncode=0)
        
        # Mock file operations
        mock_file = mock_open(read_data='edited content')()
        with patch('builtins.open', mock_open()) as m:
            # Write phase
            m.return_value.__enter__.return_value.write = Mock()
            # Read phase
            m.return_value.__enter__.return_value.read = Mock(return_value='edited content')
            
            with patch('os.fdopen', return_value=m.return_value):
                result = Editor.edit_text('initial content')
        
        # Verify
        assert result == 'edited content'
        mock_chmod.assert_called_once_with(mock_tmpfile, 0o600)
        mock_subprocess.assert_called_once()
        mock_unlink.assert_called_once_with(mock_tmpfile)
    
    @patch('tempfile.mkstemp')
    @patch('subprocess.run')
    @patch.object(Editor, '_get_editor')
    @patch.object(Editor, '_get_secure_tmpdir')
    @patch('os.chmod')
    @patch('os.unlink')
    def test_edit_text_no_changes(self, mock_unlink, mock_chmod, mock_tmpdir,
                                  mock_get_editor, mock_subprocess, mock_mkstemp):
        """Test editing with no changes returns None."""
        mock_fd = 3
        mock_tmpfile = '/tmp/lpass-test.txt'
        mock_mkstemp.return_value = (mock_fd, mock_tmpfile)
        mock_get_editor.return_value = 'vim'
        mock_tmpdir.return_value = Path('/tmp')
        mock_subprocess.return_value = Mock(returncode=0)
        
        initial_text = 'unchanged text'
        
        with patch('os.fdopen', mock_open()):
            with patch('builtins.open', mock_open(read_data=initial_text)):
                result = Editor.edit_text(initial_text)
        
        assert result is None
    
    @patch('tempfile.mkstemp')
    @patch('subprocess.run')
    @patch.object(Editor, '_get_editor')
    @patch.object(Editor, '_get_secure_tmpdir')
    @patch('os.chmod')
    @patch('os.unlink')
    def test_edit_text_editor_failure(self, mock_unlink, mock_chmod, mock_tmpdir,
                                      mock_get_editor, mock_subprocess, mock_mkstemp):
        """Test handling editor failure."""
        mock_fd = 3
        mock_tmpfile = '/tmp/lpass-test.txt'
        mock_mkstemp.return_value = (mock_fd, mock_tmpfile)
        mock_get_editor.return_value = 'vim'
        mock_tmpdir.return_value = Path('/tmp')
        mock_subprocess.return_value = Mock(returncode=1)
        
        with patch('os.fdopen', mock_open()):
            result = Editor.edit_text('initial content')
        
        assert result is None
        mock_unlink.assert_called_once()


@pytest.mark.unit
class TestEditField:
    """Tests for edit_field function."""
    
    @patch.object(Editor, 'edit_text')
    def test_edit_field_success(self, mock_edit_text):
        """Test successful field editing."""
        mock_edit_text.return_value = 'line 1\nline 2\nnew content'
        
        result = Editor.edit_field('Password', 'old password')
        
        assert result == 'line 1\nline 2\nnew content'
        # Check header was added
        call_args = mock_edit_text.call_args[0][0]
        assert '# Edit Password' in call_args
        assert 'old password' in call_args
    
    @patch.object(Editor, 'edit_text')
    def test_edit_field_cancelled(self, mock_edit_text):
        """Test field editing cancelled."""
        mock_edit_text.return_value = None
        
        result = Editor.edit_field('Username', 'olduser')
        
        assert result is None
    
    @patch.object(Editor, 'edit_text')
    def test_edit_field_removes_comments(self, mock_edit_text):
        """Test that comment lines are removed."""
        edited_text = '# This is a comment\nactual content\n# Another comment\nmore content'
        mock_edit_text.return_value = edited_text
        
        result = Editor.edit_field('Notes', '')
        
        assert '# This is a comment' not in result
        assert '# Another comment' not in result
        assert 'actual content' in result
        assert 'more content' in result


@pytest.mark.unit
class TestEditNotes:
    """Tests for edit_notes function."""
    
    @patch.object(Editor, 'edit_field')
    def test_edit_notes(self, mock_edit_field):
        """Test editing notes."""
        mock_edit_field.return_value = 'new notes'
        
        result = Editor.edit_notes('old notes')
        
        mock_edit_field.assert_called_once_with('Notes', 'old notes')
        assert result == 'new notes'


@pytest.mark.unit
class TestParseAccountTemplate:
    """Tests for _parse_account_template function."""
    
    def test_parse_basic_account(self):
        """Test parsing basic account template."""
        content = '''Name: Test Account
URL: https://example.com
Username: testuser
Password: testpass
Notes:
Some notes here'''
        
        result = Editor._parse_account_template(content, is_secure_note=False)
        
        assert result['name'] == 'Test Account'
        assert result['url'] == 'https://example.com'
        assert result['username'] == 'testuser'
        assert result['password'] == 'testpass'
        assert 'Some notes here' in result['notes']
    
    def test_parse_with_custom_fields(self):
        """Test parsing account with custom fields."""
        content = '''Name: Test Account
URL: https://example.com
Username: testuser
Password: testpass
CustomField: custom value
AnotherField: another value
Notes:
Test notes'''
        
        result = Editor._parse_account_template(content, is_secure_note=False)
        
        assert len(result['fields']) == 2
        assert any(f['name'] == 'CustomField' and f['value'] == 'custom value' 
                  for f in result['fields'])
        assert any(f['name'] == 'AnotherField' and f['value'] == 'another value'
                  for f in result['fields'])
    
    def test_parse_multiline_fields(self):
        """Test parsing fields with multiple lines."""
        content = '''Name: Test Account
Password: line1
line2
line3
Notes:
Multi
line
notes'''
        
        result = Editor._parse_account_template(content, is_secure_note=False)
        
        assert 'line1\nline2\nline3' in result['password']
        assert 'Multi\nline\nnotes' in result['notes']
    
    def test_parse_ignores_comments_in_notes(self):
        """Test that comments in notes section are ignored."""
        content = '''Name: Test Account
Notes:    # Add notes below this line.
# This is a comment
Real note content
# Another comment'''
        
        result = Editor._parse_account_template(content, is_secure_note=False)
        
        assert 'Real note content' in result['notes']
        assert '# This is a comment' not in result['notes']
        assert '# Another comment' not in result['notes']


@pytest.mark.unit
class TestEditAccountTemplate:
    """Tests for edit_account_template function."""
    
    @patch.object(Editor, 'edit_text')
    @patch.object(Editor, '_parse_account_template')
    def test_edit_account_template_success(self, mock_parse, mock_edit):
        """Test successful account template editing."""
        account_data = {
            'name': 'Test Account',
            'url': 'https://example.com',
            'username': 'user',
            'password': 'pass',
            'notes': 'Some notes',
            'fields': []
        }
        
        mock_edit.return_value = 'edited template'
        mock_parse.return_value = {
            'name': 'Edited Account',
            'url': 'https://new.com',
            'username': 'newuser',
            'password': 'newpass',
            'notes': 'New notes',
            'fields': []
        }
        
        result = Editor.edit_account_template(account_data)
        
        assert result is not None
        assert result['name'] == 'Edited Account'
        assert result['url'] == 'https://new.com'
    
    @patch.object(Editor, 'edit_text')
    def test_edit_account_template_cancelled(self, mock_edit):
        """Test cancelled account template editing."""
        account_data = {'name': 'Test', 'url': '', 'username': '', 'password': '', 'notes': '', 'fields': []}
        mock_edit.return_value = None
        
        result = Editor.edit_account_template(account_data)
        
        assert result is None

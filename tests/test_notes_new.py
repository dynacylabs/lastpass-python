"""Tests for notes module (secure note expansion/collapse)."""
import pytest
from copy import deepcopy

from lastpass.notes import is_secure_note, notes_expand, notes_collapse
from lastpass.models import Account, Field


@pytest.mark.unit
class TestIsSecureNote:
    """Tests for is_secure_note function."""
    
    def test_is_secure_note_true(self):
        """Test identifying secure note."""
        account = Account(
            id='123',
            name='My Secure Note',
            url='http://sn',
            username='',
            password='',
            notes='NoteType:Generic\nContent:test'
        )
        
        assert is_secure_note(account)
    
    def test_is_secure_note_false(self):
        """Test regular account is not secure note."""
        account = Account(
            id='123',
            name='Regular Account',
            url='https://example.com',
            username='user',
            password='pass',
            notes=''
        )
        
        assert not is_secure_note(account)
    
    def test_is_secure_note_http_sn_url(self):
        """Test http://sn URL identifies secure note."""
        account = Account(id='1', name='Note', url='http://sn', username='', password='', notes='')
        assert is_secure_note(account)
    
    def test_is_secure_note_other_url(self):
        """Test other URLs don't identify as secure note."""
        account = Account(id='1', name='Site', url='http://example.com', username='', password='', notes='')
        assert not is_secure_note(account)


@pytest.mark.unit
class TestNotesExpand:
    """Tests for notes_expand function."""
    
    def test_expand_basic_secure_note(self):
        """Test expanding basic secure note."""
        account = Account(
            id='123',
            name='My Note',
            url='http://sn',
            username='',
            password='',
            notes='NoteType:Generic\nUsername:testuser\nPassword:testpass\nNotes:Some notes'
        )
        
        expanded = notes_expand(account)
        
        assert expanded is not None
        assert expanded.username == 'testuser'
        assert expanded.password == 'testpass'
        assert 'Some notes' in expanded.notes
    
    def test_expand_with_custom_fields(self):
        """Test expanding note with custom fields."""
        account = Account(
            id='123',
            name='SSH Key',
            url='http://sn',
            username='',
            password='',
            notes='NoteType:SSH Key\nHostname:server.com\nPort:22\nUsername:admin'
        )
        
        expanded = notes_expand(account)
        
        assert expanded is not None
        assert any(f.name == 'Hostname' and f.value == 'server.com' for f in expanded.fields)
        assert any(f.name == 'Port' and f.value == '22' for f in expanded.fields)
        assert expanded.username == 'admin'
    
    def test_expand_with_multiline_field(self):
        """Test expanding note with multiline field values."""
        account = Account(
            id='123',
            name='Private Key',
            url='http://sn',
            username='',
            password='',
            notes='NoteType:SSH Key\nPrivateKey:-----BEGIN RSA PRIVATE KEY-----\nMIIEpAIBAAKC...\n-----END RSA PRIVATE KEY-----'
        )
        
        expanded = notes_expand(account)
        
        assert expanded is not None
        private_key_field = next((f for f in expanded.fields if f.name == 'PrivateKey'), None)
        assert private_key_field is not None
        assert '-----BEGIN RSA PRIVATE KEY-----' in private_key_field.value
        assert '-----END RSA PRIVATE KEY-----' in private_key_field.value
    
    def test_expand_non_secure_note_returns_none(self):
        """Test expanding regular account returns None."""
        account = Account(
            id='123',
            name='Regular Site',
            url='https://example.com',
            username='user',
            password='pass',
            notes='Regular notes'
        )
        
        expanded = notes_expand(account)
        assert expanded is None
    
    def test_expand_without_notetype_returns_none(self):
        """Test expanding note without NoteType returns None."""
        account = Account(
            id='123',
            name='Invalid Note',
            url='http://sn',
            username='',
            password='',
            notes='Username:test\nPassword:pass'
        )
        
        expanded = notes_expand(account)
        assert expanded is None
    
    def test_expand_preserves_account_metadata(self):
        """Test that expansion preserves account ID, name, group."""
        account = Account(
            id='456',
            name='Test Note',
            group='Folder/Subfolder',
            fullname='Folder/Subfolder/Test Note',
            url='http://sn',
            username='',
            password='',
            notes='NoteType:Generic\nUsername:user',
            share=None,
            pwprotect='off'
        )
        
        expanded = notes_expand(account)
        
        assert expanded.id == '456'
        assert expanded.name == 'Test Note'
        assert expanded.group == 'Folder/Subfolder'
        assert expanded.fullname == 'Folder/Subfolder/Test Note'
        assert expanded.share == account.share
        assert expanded.pwprotect == 'off'
    
    def test_expand_url_field_special_handling(self):
        """Test that URL field is extracted properly."""
        account = Account(
            id='123',
            name='Website Note',
            url='http://sn',
            username='',
            password='',
            notes='NoteType:Generic\nURL:https://example.com\nUsername:user'
        )
        
        expanded = notes_expand(account)
        
        assert expanded.url == 'https://example.com'
        assert expanded.username == 'user'
    
    def test_expand_notes_section(self):
        """Test that Notes: section is handled correctly."""
        account = Account(
            id='123',
            name='Note with Notes',
            url='http://sn',
            username='',
            password='',
            notes='NoteType:Generic\nUsername:user\nNotes:Line 1\nLine 2\nLine 3'
        )
        
        expanded = notes_expand(account)
        
        assert 'Line 1\nLine 2\nLine 3' in expanded.notes


@pytest.mark.unit
class TestNotesCollapse:
    """Tests for notes_collapse function."""
    
    def test_collapse_basic_account(self):
        """Test collapsing basic account to secure note."""
        account = Account(
            id='123',
            name='My Account',
            url='https://example.com',
            username='testuser',
            password='testpass',
            notes='Some notes',
            fields=[Field(name='NoteType', value='Generic', type='text')]
        )
        
        collapsed = notes_collapse(account)
        
        assert collapsed.url == 'http://sn'
        assert 'NoteType:Generic' in collapsed.notes
        assert 'Username:testuser' in collapsed.notes
        assert 'Password:testpass' in collapsed.notes
        assert 'Notes:Some notes' in collapsed.notes
    
    def test_collapse_with_custom_fields(self):
        """Test collapsing account with custom fields."""
        account = Account(
            id='123',
            name='SSH Key',
            url='',
            username='admin',
            password='',
            notes='',
            fields=[
                Field(name='NoteType', value='SSH Key', type='text'),
                Field(name='Hostname', value='server.com', type='text'),
                Field(name='Port', value='22', type='text')
            ]
        )
        
        collapsed = notes_collapse(account)
        
        assert 'NoteType:SSH Key' in collapsed.notes
        assert 'Hostname:server.com' in collapsed.notes
        assert 'Port:22' in collapsed.notes
        assert 'Username:admin' in collapsed.notes
    
    def test_collapse_notetype_first(self):
        """Test that NoteType appears first in collapsed notes."""
        account = Account(
            id='123',
            name='Note',
            url='',
            username='',
            password='',
            notes='',
            fields=[
                Field(name='CustomField', value='custom', type='text'),
                Field(name='NoteType', value='Generic', type='text'),
                Field(name='AnotherField', value='another', type='text')
            ]
        )
        
        collapsed = notes_collapse(account)
        
        lines = collapsed.notes.split('\n')
        assert lines[0] == 'NoteType:Generic'
    
    def test_collapse_preserves_metadata(self):
        """Test that collapse preserves account metadata."""
        account = Account(
            id='789',
            name='Test Note',
            group='Folder',
            fullname='Folder/Test Note',
            url='https://example.com',
            username='user',
            password='pass',
            notes='notes',
            share=None,
            pwprotect='on',
            fields=[Field(name='NoteType', value='Generic', type='text')]
        )
        
        collapsed = notes_collapse(account)
        
        assert collapsed.id == '789'
        assert collapsed.name == 'Test Note'
        assert collapsed.group == 'Folder'
        assert collapsed.fullname == 'Folder/Test Note'
        assert collapsed.pwprotect == 'on'
    
    def test_collapse_empty_fields_omitted(self):
        """Test that empty fields are omitted from collapsed notes."""
        account = Account(
            id='123',
            name='Sparse Note',
            url='',
            username='',
            password='',
            notes='',
            fields=[Field(name='NoteType', value='Generic', type='text')]
        )
        
        collapsed = notes_collapse(account)
        
        # Should only have NoteType
        assert collapsed.notes == 'NoteType:Generic'
    
    def test_collapse_strips_whitespace(self):
        """Test that field values are stripped."""
        account = Account(
            id='123',
            name='Note',
            url='  https://example.com  ',
            username='  user  ',
            password='  pass  ',
            notes='  notes  ',
            fields=[Field(name='NoteType', value='  Generic  ', type='text')]
        )
        
        collapsed = notes_collapse(account)
        
        assert 'NoteType:Generic' in collapsed.notes
        assert 'Username:user' in collapsed.notes
        assert 'Password:pass' in collapsed.notes
        assert 'URL:https://example.com' in collapsed.notes
        assert 'Notes:notes' in collapsed.notes
    
    def test_collapse_non_sn_url_included(self):
        """Test that non-sn URLs are included in collapsed notes."""
        account = Account(
            id='123',
            name='Note',
            url='https://example.com',
            username='user',
            password='pass',
            notes='',
            fields=[Field(name='NoteType', value='Generic', type='text')]
        )
        
        collapsed = notes_collapse(account)
        
        assert 'URL:https://example.com' in collapsed.notes
    
    def test_collapse_http_sn_url_excluded(self):
        """Test that http://sn URL is not included in notes."""
        account = Account(
            id='123',
            name='Note',
            url='http://sn',
            username='user',
            password='',
            notes='',
            fields=[Field(name='NoteType', value='Generic', type='text')]
        )
        
        collapsed = notes_collapse(account)
        
        # URL line should not appear for http://sn
        assert 'URL:http://sn' not in collapsed.notes
        # But other fields should be there
        assert 'NoteType:Generic' in collapsed.notes
        assert 'Username:user' in collapsed.notes


@pytest.mark.unit
class TestNotesRoundtrip:
    """Tests for expand/collapse roundtrip."""
    
    def test_roundtrip_preserves_data(self):
        """Test that expand then collapse preserves data."""
        original = Account(
            id='123',
            name='Test Note',
            url='http://sn',
            username='',
            password='',
            notes='NoteType:Generic\nUsername:testuser\nPassword:testpass\nCustomField:value\nNotes:Some notes here'
        )
        
        expanded = notes_expand(original)
        collapsed = notes_collapse(expanded)
        re_expanded = notes_expand(collapsed)
        
        assert re_expanded.username == expanded.username
        assert re_expanded.password == expanded.password
        assert re_expanded.notes == expanded.notes
        assert len(re_expanded.fields) == len(expanded.fields)

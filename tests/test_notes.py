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
        assert expanded.notes == 'Some notes'
    
    def test_expand_not_secure_note(self):
        """Test expanding non-secure note returns None."""
        account = Account(
            id='123',
            name='Regular',
            url='https://example.com',
            username='user',
            password='pass',
            notes='Regular notes'
        )
        
        result = notes_expand(account)
        assert result is None
    
    def test_expand_without_notetype_header(self):
        """Test expanding note without NoteType header."""
        account = Account(
            id='123',
            name='Note',
            url='http://sn',
            username='',
            password='',
            notes='Just some text without NoteType'
        )
        
        result = notes_expand(account)
        assert result is None
    
    def test_expand_custom_fields(self):
        """Test expanding note with custom fields."""
        account = Account(
            id='123',
            name='Credit Card',
            url='http://sn',
            username='',
            password='',
            notes='NoteType:Credit Card\nNumber:1234567890\nCVV:123\nExpiration:12/25'
        )
        
        expanded = notes_expand(account)
        
        assert expanded is not None
        assert len(expanded.fields) >= 2  # At least Number and other fields
        
        # Find Number field
        number_field = next((f for f in expanded.fields if f.name == 'Number'), None)
        assert number_field is not None
        assert number_field.value == '1234567890'
    
    def test_expand_multiline_notes(self):
        """Test expanding note with multiline notes section."""
        account = Account(
            id='123',
            name='Note',
            url='http://sn',
            username='',
            password='',
            notes='NoteType:Generic\nUsername:user\nNotes:Line 1\nLine 2\nLine 3'
        )
        
        expanded = notes_expand(account)
        
        assert expanded is not None
        assert 'Line 1' in expanded.notes
        assert 'Line 2' in expanded.notes
        assert 'Line 3' in expanded.notes
    
    def test_expand_with_url(self):
        """Test expanding note with URL field."""
        account = Account(
            id='123',
            name='Note',
            url='http://sn',
            username='',
            password='',
            notes='NoteType:Generic\nURL:https://example.com\nUsername:user'
        )
        
        expanded = notes_expand(account)
        
        assert expanded is not None
        assert expanded.url == 'https://example.com'
    
    def test_expand_empty_fields(self):
        """Test expanding note with empty field values."""
        account = Account(
            id='123',
            name='Note',
            url='http://sn',
            username='',
            password='',
            notes='NoteType:Generic\nUsername:\nPassword:\nNotes:'
        )
        
        expanded = notes_expand(account)
        
        assert expanded is not None
        assert expanded.username == ''
        assert expanded.password == ''
        # NoteType is stored as a field, notes field should be empty
        assert expanded.notes == ''
        assert any(f.name == 'NoteType' and f.value == 'Generic' for f in expanded.fields)
    
    def test_expand_preserves_account_properties(self):
        """Test that expansion preserves other account properties."""
        account = Account(
            id='123',
            name='Note',
            group='Work/Important',
            fullname='Work/Important/Note',
            url='http://sn',
            username='',
            password='',
            notes='NoteType:Generic\nUsername:user',
            share='shared-folder',
            pwprotect=True,
            attachments=['file1', 'file2'],
            attachkey='key123',
            attach_present=True
        )
        
        expanded = notes_expand(account)
        
        assert expanded is not None
        assert expanded.id == '123'
        assert expanded.name == 'Note'
        assert expanded.group == 'Work/Important'
        assert expanded.fullname == 'Work/Important/Note'
        assert expanded.share == 'shared-folder'
        assert expanded.pwprotect is True
        assert expanded.attachments == ['file1', 'file2']
        assert expanded.attachkey == 'key123'
        assert expanded.attach_present is True


@pytest.mark.unit
class TestNotesCollapse:
    """Tests for notes_collapse function."""
    
    def test_collapse_basic_account(self):
        """Test collapsing basic account."""
        account = Account(
            id='123',
            name='Note',
            url='',
            username='testuser',
            password='testpass',
            notes='Some notes',
            fields=[Field(name='NoteType', value='Generic', type='text')]
        )
        
        collapsed = notes_collapse(account)
        
        assert collapsed is not None
        assert collapsed.url == 'http://sn'
        assert 'NoteType:Generic' in collapsed.notes
        assert 'Username:testuser' in collapsed.notes
        assert 'Password:testpass' in collapsed.notes
        assert 'Notes:Some notes' in collapsed.notes
    
    def test_collapse_with_custom_fields(self):
        """Test collapsing account with custom fields."""
        account = Account(
            id='123',
            name='Credit Card',
            url='',
            username='',
            password='',
            notes='',
            fields=[
                Field(name='NoteType', value='Credit Card', type='text'),
                Field(name='Number', value='1234567890', type='text'),
                Field(name='CVV', value='123', type='text'),
                Field(name='Expiration', value='12/25', type='text')
            ]
        )
        
        collapsed = notes_collapse(account)
        
        assert collapsed is not None
        assert 'NoteType:Credit Card' in collapsed.notes
        assert 'Number:1234567890' in collapsed.notes
        assert 'CVV:123' in collapsed.notes
        assert 'Expiration:12/25' in collapsed.notes
    
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
                Field(name='CustomField', value='value1', type='text'),
                Field(name='NoteType', value='Generic', type='text'),
                Field(name='AnotherField', value='value2', type='text')
            ]
        )
        
        collapsed = notes_collapse(account)
        
        lines = collapsed.notes.split('\n')
        assert lines[0] == 'NoteType:Generic'
    
    def test_collapse_strips_whitespace(self):
        """Test that collapse strips leading/trailing whitespace."""
        account = Account(
            id='123',
            name='Note',
            url=' https://example.com ',
            username=' user ',
            password=' pass ',
            notes=' notes content ',
            fields=[Field(name='NoteType', value=' Generic ', type='text')]
        )
        
        collapsed = notes_collapse(account)
        
        assert 'NoteType:Generic' in collapsed.notes
        assert 'Username:user' in collapsed.notes
        assert 'Password:pass' in collapsed.notes
        assert 'URL:https://example.com' in collapsed.notes
    
    def test_collapse_skips_http_sn_url(self):
        """Test that http://sn URL is not included in notes."""
        account = Account(
            id='123',
            name='Note',
            url='http://sn',
            username='user',
            password='pass',
            notes='',
            fields=[Field(name='NoteType', value='Generic', type='text')]
        )
        
        collapsed = notes_collapse(account)
        
        # Should not have URL:http://sn in notes
        assert 'URL:http://sn' not in collapsed.notes
    
    def test_collapse_empty_fields_skipped(self):
        """Test that empty fields are skipped."""
        account = Account(
            id='123',
            name='Note',
            url='',
            username='',
            password='',
            notes='',
            fields=[Field(name='NoteType', value='Generic', type='text')]
        )
        
        collapsed = notes_collapse(account)
        
        # Should only have NoteType
        lines = [line for line in collapsed.notes.split('\n') if line.strip()]
        assert len(lines) == 1
        assert lines[0] == 'NoteType:Generic'
    
    def test_collapse_preserves_account_properties(self):
        """Test that collapse preserves other account properties."""
        account = Account(
            id='123',
            name='Note',
            group='Work',
            fullname='Work/Note',
            url='',
            username='user',
            password='pass',
            notes='',
            share='shared',
            pwprotect=True,
            attachments=['file'],
            attachkey='key',
            attach_present=True,
            fields=[Field(name='NoteType', value='Generic', type='text')]
        )
        
        collapsed = notes_collapse(account)
        
        assert collapsed.id == '123'
        assert collapsed.name == 'Note'
        assert collapsed.group == 'Work'
        assert collapsed.fullname == 'Work/Note'
        assert collapsed.share == 'shared'
        assert collapsed.pwprotect is True
        assert collapsed.attachments == ['file']
        assert collapsed.attachkey == 'key'
        assert collapsed.attach_present is True


@pytest.mark.unit
class TestNotesRoundTrip:
    """Tests for expand/collapse round-trip."""
    
    def test_round_trip_preserves_data(self):
        """Test that expand followed by collapse preserves data."""
        original = Account(
            id='123',
            name='Note',
            url='http://sn',
            username='',
            password='',
            notes='NoteType:Generic\nUsername:user\nPassword:pass\nURL:https://example.com\nCustomField:value\nNotes:My notes'
        )
        
        # Expand then collapse
        expanded = notes_expand(original)
        collapsed = notes_collapse(expanded)
        
        # Verify collapsed has correct structure
        assert collapsed.url == 'http://sn'
        assert 'Username:user' in collapsed.notes
        assert 'Password:pass' in collapsed.notes
        
        # Expand again to compare
        final = notes_expand(collapsed)
        
        # Final should not be None if collapse worked correctly
        assert final is not None, f"notes_expand returned None for collapsed account with url={collapsed.url} and notes={collapsed.notes[:100]}"
        assert final.username == expanded.username
        assert final.password == expanded.password
        assert final.url == expanded.url

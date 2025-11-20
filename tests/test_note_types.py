"""
Tests for secure note types functionality
"""

import pytest
from lastpass.note_types import (
    NoteType,
    get_note_type_by_shortname,
    get_note_type_by_name,
    get_template,
    format_note_fields,
    parse_note_fields,
    is_multiline_field,
    has_field,
)


class TestNoteTypeEnum:
    """Test NoteType enum"""
    
    def test_has_all_expected_types(self):
        """Test NoteType enum has all expected types"""
        assert NoteType.CREDIT is not None
        assert NoteType.BANK is not None
        assert NoteType.SSH_KEY is not None
        assert NoteType.SERVER is not None
        assert NoteType.WIFI is not None
        assert NoteType.PASSPORT is not None
        assert NoteType.AMEX is not None
        assert NoteType.VISA is not None
        assert NoteType.MASTERCARD is not None
        assert NoteType.DATABASE is not None
        assert NoteType.DRIVERS_LICENSE is not None
        assert NoteType.EMAIL is not None
        assert NoteType.HEALTH_INSURANCE is not None
        assert NoteType.IM is not None
        assert NoteType.INSURANCE is not None
        assert NoteType.MEMBERSHIP is not None
        assert NoteType.SOFTWARE_LICENSE is not None
        assert NoteType.SSN is not None


class TestNoteTypeLookup:
    """Test note type lookup functions"""
    
    def test_get_note_type_by_shortname(self):
        """Test getting note type by shortname"""
        assert get_note_type_by_shortname("creditcard") == NoteType.CREDIT
        assert get_note_type_by_shortname("sshkey") == NoteType.SSH_KEY
        assert get_note_type_by_shortname("server") == NoteType.SERVER
        assert get_note_type_by_shortname("wifi") == NoteType.WIFI
        assert get_note_type_by_shortname("bank") == NoteType.BANK
        assert get_note_type_by_shortname("passport") == NoteType.PASSPORT
        
    def test_get_note_type_by_shortname_case_insensitive(self):
        """Test shortname lookup is case insensitive"""
        assert get_note_type_by_shortname("CreditCard") == NoteType.CREDIT
        assert get_note_type_by_shortname("SSHKEY") == NoteType.SSH_KEY
        
    def test_get_note_type_by_shortname_invalid(self):
        """Test invalid shortname returns None"""
        assert get_note_type_by_shortname("invalid") is None
        assert get_note_type_by_shortname("nonexistent") is None
        
    def test_get_note_type_by_name(self):
        """Test getting note type by full name"""
        assert get_note_type_by_name("Credit Card") == NoteType.CREDIT
        assert get_note_type_by_name("SSH Key") == NoteType.SSH_KEY
        assert get_note_type_by_name("Bank Account") == NoteType.BANK
        assert get_note_type_by_name("WiFi Password") == NoteType.WIFI
        
    def test_get_note_type_by_name_case_insensitive(self):
        """Test name lookup is case insensitive"""
        assert get_note_type_by_name("credit card") == NoteType.CREDIT
        assert get_note_type_by_name("CREDIT CARD") == NoteType.CREDIT


class TestNoteTemplates:
    """Test note type templates"""
    
    def test_get_template_credit_card(self):
        """Test getting credit card template"""
        template = get_template(NoteType.CREDIT)
        assert template is not None
        assert template.shortname == "creditcard"
        assert template.name == "Credit Card"
        assert "Number" in template.fields
        assert "Expiration Date" in template.fields
        assert "Security Code" in template.fields
        assert "Name on Card" in template.fields
        
    def test_get_template_ssh_key(self):
        """Test getting SSH key template"""
        template = get_template(NoteType.SSH_KEY)
        assert template is not None
        assert template.shortname == "sshkey"
        assert template.name == "SSH Key"
        assert "Private Key" in template.fields
        assert "Public Key" in template.fields
        assert "Hostname" in template.fields
        
    def test_ssh_key_multiline_fields(self):
        """Test SSH key template has multiline fields"""
        template = get_template(NoteType.SSH_KEY)
        assert template.multiline_fields is not None
        assert "Private Key" in template.multiline_fields
        assert "Public Key" in template.multiline_fields
        
    def test_get_template_bank_account(self):
        """Test getting bank account template"""
        template = get_template(NoteType.BANK)
        assert template is not None
        assert "Bank Name" in template.fields
        assert "Account Number" in template.fields
        assert "Routing Number" in template.fields
        
    def test_get_template_server(self):
        """Test getting server template"""
        template = get_template(NoteType.SERVER)
        assert template is not None
        assert "Hostname" in template.fields
        assert "Username" in template.fields
        assert "Password" in template.fields


class TestNoteFieldOperations:
    """Test note field operations"""
    
    def test_is_multiline_field(self):
        """Test checking if field is multiline"""
        assert is_multiline_field(NoteType.SSH_KEY, "Private Key") is True
        assert is_multiline_field(NoteType.SSH_KEY, "Public Key") is True
        assert is_multiline_field(NoteType.SSH_KEY, "Hostname") is False
        assert is_multiline_field(NoteType.CREDIT, "Number") is False
        
    def test_has_field(self):
        """Test checking if note type has a field"""
        assert has_field(NoteType.CREDIT, "Number") is True
        assert has_field(NoteType.CREDIT, "Expiration Date") is True
        assert has_field(NoteType.CREDIT, "InvalidField") is False
        assert has_field(NoteType.SSH_KEY, "Private Key") is True
        assert has_field(NoteType.SSH_KEY, "Number") is False


class TestNoteFormatting:
    """Test note field formatting and parsing"""
    
    def test_format_note_fields_credit_card(self):
        """Test formatting credit card note fields"""
        fields = {
            "Number": "1234-5678-9012-3456",
            "Expiration Date": "12/25",
            "Name on Card": "John Doe",
            "Security Code": "123"
        }
        
        result = format_note_fields(NoteType.CREDIT, fields)
        assert "NoteType:Credit Card" in result
        assert "Number:1234-5678-9012-3456" in result
        assert "Expiration Date:12/25" in result
        assert "Name on Card:John Doe" in result
        
    def test_format_note_fields_server(self):
        """Test formatting server note fields"""
        fields = {
            "Hostname": "server.example.com",
            "Username": "admin",
            "Password": "secret123"
        }
        
        result = format_note_fields(NoteType.SERVER, fields)
        assert "NoteType:Server" in result
        assert "Hostname:server.example.com" in result
        assert "Username:admin" in result
        assert "Password:secret123" in result
        
    def test_format_note_fields_generic(self):
        """Test formatting generic note fields"""
        fields = {
            "CustomField1": "value1",
            "CustomField2": "value2"
        }
        
        result = format_note_fields(NoteType.GENERIC, fields)
        assert "CustomField1:value1" in result
        assert "CustomField2:value2" in result
        assert "NoteType" not in result  # Generic notes don't have type header
        
    def test_parse_note_fields_credit_card(self):
        """Test parsing credit card note fields"""
        notes = """NoteType:Credit Card
Number:1234-5678-9012-3456
Expiration Date:12/25
Name on Card:John Doe
Security Code:123"""
        
        note_type, fields = parse_note_fields(notes)
        assert note_type == NoteType.CREDIT
        assert fields["Number"] == "1234-5678-9012-3456"
        assert fields["Expiration Date"] == "12/25"
        assert fields["Name on Card"] == "John Doe"
        assert fields["Security Code"] == "123"
        
    def test_parse_note_fields_server(self):
        """Test parsing server note fields"""
        notes = """NoteType:Server
Hostname:server.example.com
Username:admin
Password:secret123"""
        
        note_type, fields = parse_note_fields(notes)
        assert note_type == NoteType.SERVER
        assert fields["Hostname"] == "server.example.com"
        assert fields["Username"] == "admin"
        assert fields["Password"] == "secret123"
        
    def test_parse_note_fields_generic(self):
        """Test parsing generic note fields"""
        notes = """CustomField1:value1
CustomField2:value2
AnotherField:value3"""
        
        note_type, fields = parse_note_fields(notes)
        assert note_type == NoteType.GENERIC
        assert fields["CustomField1"] == "value1"
        assert fields["CustomField2"] == "value2"
        assert fields["AnotherField"] == "value3"
        
    def test_parse_note_fields_handles_colons_in_values(self):
        """Test parsing handles colons in field values"""
        notes = """NoteType:Server
Hostname:server.example.com
URL:https://example.com:8080"""
        
        note_type, fields = parse_note_fields(notes)
        assert fields["URL"] == "https://example.com:8080"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

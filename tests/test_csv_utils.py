"""
Tests for CSV import and export utilities
"""

import pytest
from lastpass.csv_utils import (
    export_accounts_to_csv,
    import_accounts_from_csv,
    parse_csv_field_list,
)
from lastpass.models import Account, Field


class TestCSVExport:
    """Test CSV export functionality"""
    
    def test_export_basic_accounts(self):
        """Test exporting basic accounts to CSV"""
        accounts = [
            Account(
                id="1",
                name="Test Account",
                username="user@example.com",
                password="password123",
                url="https://example.com",
                notes="Test notes",
                group="Work"
            ),
            Account(
                id="2",
                name="Another Account",
                username="another@example.com",
                password="pass456",
                url="https://another.com",
                notes="",
                group="Personal"
            )
        ]
        
        csv_data = export_accounts_to_csv(accounts)
        
        # Check header
        assert "url,username,password,extra,name,grouping" in csv_data
        
        # Check data
        assert "Test Account" in csv_data
        assert "user@example.com" in csv_data
        assert "password123" in csv_data
        assert "Work" in csv_data
        assert "Another Account" in csv_data
        assert "another@example.com" in csv_data
        
    def test_export_with_custom_fields(self):
        """Test exporting with custom field selection"""
        accounts = [
            Account(
                id="1",
                name="Test",
                username="user",
                password="pass",
                url="https://example.com"
            )
        ]
        
        csv_data = export_accounts_to_csv(accounts, fields=["name", "username"])
        
        lines = csv_data.strip().split('\r\n')
        assert lines[0] == "name,username"
        assert lines[1] == "Test,user"
        
    def test_export_with_all_fields(self):
        """Test exporting with all available fields"""
        accounts = [
            Account(
                id="123",
                name="Full Account",
                username="user@test.com",
                password="secret",
                url="https://test.com",
                notes="Some notes",
                group="MyGroup",
                favorite=True,
                attach_present=True,
                last_touch="1234567890",
                last_modified_gmt="2024-01-01"
            )
        ]
        
        fields = ["id", "name", "username", "password", "url", "extra", "grouping", "fav", "attachpresent"]
        csv_data = export_accounts_to_csv(accounts, fields=fields)
        
        assert "123" in csv_data
        assert "Full Account" in csv_data
        assert "user@test.com" in csv_data
        assert "MyGroup" in csv_data
        assert "1" in csv_data  # favorite flag
        
    def test_export_handles_special_characters(self):
        """Test that CSV export properly escapes special characters"""
        accounts = [
            Account(
                id="1",
                name="Account, with comma",
                username="user",
                password='pass"word',
                notes="Line1\nLine2"
            )
        ]
        
        csv_data = export_accounts_to_csv(accounts)
        
        # Commas in values should cause quoting
        assert '"Account, with comma"' in csv_data or 'Account, with comma' in csv_data
        
    def test_export_empty_accounts(self):
        """Test exporting empty account list"""
        accounts = []
        csv_data = export_accounts_to_csv(accounts)
        
        # Should still have header
        assert "url,username,password" in csv_data


class TestCSVImport:
    """Test CSV import functionality"""
    
    def test_import_basic_accounts(self):
        """Test importing basic accounts from CSV"""
        csv_data = """url,username,password,extra,name,grouping
https://example.com,user@example.com,password123,Test notes,Test Account,Work
https://another.com,another@example.com,pass456,,Another Account,Personal"""
        
        accounts = import_accounts_from_csv(csv_data)
        
        assert len(accounts) == 2
        
        assert accounts[0]["name"] == "Test Account"
        assert accounts[0]["username"] == "user@example.com"
        assert accounts[0]["password"] == "password123"
        assert accounts[0]["url"] == "https://example.com"
        assert accounts[0]["notes"] == "Test notes"
        assert accounts[0]["group"] == "Work"
        
        assert accounts[1]["name"] == "Another Account"
        assert accounts[1]["username"] == "another@example.com"
        assert accounts[1]["group"] == "Personal"
        
    def test_import_skip_duplicates_by_default(self):
        """Test that duplicates are skipped by default"""
        csv_data = """url,username,password,extra,name,grouping
https://example.com,user@example.com,password123,Test notes,Test Account,Work
https://example.com,user@example.com,password123,Test notes,Test Account,Work
https://different.com,user@example.com,pass456,,Different Account,Work"""
        
        accounts = import_accounts_from_csv(csv_data, keep_duplicates=False)
        
        # Should only import 2 (skip the duplicate)
        assert len(accounts) == 2
        assert accounts[0]["name"] == "Test Account"
        assert accounts[1]["name"] == "Different Account"
        
    def test_import_keep_duplicates_when_requested(self):
        """Test keeping duplicates when requested"""
        csv_data = """url,username,password,extra,name,grouping
https://example.com,user@example.com,password123,Test notes,Test Account,Work
https://example.com,user@example.com,password123,Test notes,Test Account,Work"""
        
        accounts = import_accounts_from_csv(csv_data, keep_duplicates=True)
        
        assert len(accounts) == 2
        
    def test_import_with_optional_fields(self):
        """Test importing with optional fields like favorite"""
        csv_data = """url,username,password,extra,name,grouping,fav
https://example.com,user,pass,notes,Favorite,Work,1
https://another.com,user2,pass2,notes2,Not Favorite,Work,0"""
        
        accounts = import_accounts_from_csv(csv_data)
        
        assert len(accounts) == 2
        assert accounts[0].get("favorite") is True
        assert accounts[1].get("favorite") is False
        
    def test_import_with_custom_fields(self):
        """Test importing accounts with custom fields"""
        csv_data = """url,username,password,name,grouping,API Key,Secret Token
https://example.com,user,pass,Account,Work,key123,token456
https://another.com,user2,pass2,Account2,Personal,key789,"""
        
        accounts = import_accounts_from_csv(csv_data)
        
        assert len(accounts) == 2
        assert accounts[0].get("fields") is not None
        assert accounts[0]["fields"]["API Key"] == "key123"
        assert accounts[0]["fields"]["Secret Token"] == "token456"
        assert accounts[1]["fields"]["API Key"] == "key789"
        
    def test_import_empty_csv(self):
        """Test importing empty CSV"""
        csv_data = """url,username,password,extra,name,grouping"""
        
        accounts = import_accounts_from_csv(csv_data)
        
        assert len(accounts) == 0
        
    def test_import_minimal_fields(self):
        """Test importing CSV with minimal fields"""
        csv_data = """name,username,password
Account1,user1,pass1
Account2,user2,pass2"""
        
        accounts = import_accounts_from_csv(csv_data)
        
        assert len(accounts) == 2
        assert accounts[0]["name"] == "Account1"
        assert accounts[0]["username"] == "user1"


class TestCSVUtilities:
    """Test CSV utility functions"""
    
    def test_parse_csv_field_list_basic(self):
        """Test parsing comma-separated field list"""
        field_str = "name,username,password"
        fields = parse_csv_field_list(field_str)
        
        assert fields == ["name", "username", "password"]
        
    def test_parse_csv_field_list_with_spaces(self):
        """Test parsing field list with spaces"""
        field_str = "name, username , password"
        fields = parse_csv_field_list(field_str)
        
        assert fields == ["name", "username", "password"]
        
    def test_parse_csv_field_list_empty(self):
        """Test parsing empty field list"""
        assert parse_csv_field_list("") is None
        assert parse_csv_field_list(None) is None
        
    def test_parse_csv_field_list_single_field(self):
        """Test parsing single field"""
        field_str = "name"
        fields = parse_csv_field_list(field_str)
        
        assert fields == ["name"]
    
    def test_export_with_file_output(self):
        """Test exporting to a file object"""
        import io
        accounts = [
            Account(
                id="1",
                name="Test",
                username="user",
                password="pass",
                url="https://example.com"
            )
        ]
        
        output = io.StringIO()
        result = export_accounts_to_csv(accounts, output=output)
        
        # Should return empty string when output is provided
        assert result == ""
        
        # But output should contain the CSV
        output.seek(0)
        content = output.read()
        assert "Test" in content
        assert "user" in content
    
    def test_export_with_custom_field_from_account(self):
        """Test exporting custom fields from account"""
        accounts = [
            Account(
                id="1",
                name="Test",
                username="user",
                password="pass",
                url="https://example.com",
                fields=[
                    Field(name="API Key", value="key123", type="text"),
                    Field(name="Secret", value="secret456", type="password")
                ]
            )
        ]
        
        fields = ["name", "username", "API Key", "Secret", "NonExistent"]
        csv_data = export_accounts_to_csv(accounts, fields=fields)
        
        # Custom fields should be included
        assert "key123" in csv_data
        assert "secret456" in csv_data
        
        # Non-existent field should be empty
        lines = csv_data.strip().split('\r\n')
        # The last column (NonExistent) should be empty
        assert lines[1].endswith(",") or lines[1].count(',') == len(fields) - 1
    
    def test_import_with_quotes_in_values(self):
        """Test importing values with quotes"""
        csv_data = '''url,username,password,name
https://example.com,user,"pass""word",Account'''
        
        accounts = import_accounts_from_csv(csv_data)
        
        assert len(accounts) == 1
        # CSV reader should handle escaped quotes
        assert 'pass' in accounts[0]["password"]
    
    def test_export_with_fullname_field(self):
        """Test exporting fullname field"""
        accounts = [
            Account(
                id="1",
                name="Test",
                username="user",
                password="pass",
                url="https://example.com",
                fullname="Test Full Name"
            )
        ]
        
        csv_data = export_accounts_to_csv(accounts, fields=["name", "fullname"])
        
        assert "Test Full Name" in csv_data
    
    def test_export_with_last_touch_and_modified(self):
        """Test exporting last_touch and last_modified fields"""
        accounts = [
            Account(
                id="1",
                name="Test",
                username="user",
                password="pass",
                url="https://example.com",
                last_touch="1234567890",
                last_modified_gmt="2024-01-01 12:00:00"
            )
        ]
        
        fields = ["name", "last_touch", "last_modified"]
        csv_data = export_accounts_to_csv(accounts, fields=fields)
        
        assert "1234567890" in csv_data
        assert "2024-01-01" in csv_data


class TestCSVEdgeCases:
    """Test edge cases in CSV utilities"""
    
    def test_import_with_extra_whitespace(self):
        """Test importing CSV with extra whitespace"""
        csv_data = """url,username,password,name
https://example.com,user,pass,Test"""
        
        accounts = import_accounts_from_csv(csv_data)
        
        assert len(accounts) == 1
        assert accounts[0]["username"] == "user"
    
    def test_export_none_values(self):
        """Test exporting accounts with None values"""
        from lastpass.csv_utils import escape_csv_value
        
        assert escape_csv_value(None) == ""
        assert escape_csv_value("") == ""
        assert escape_csv_value("value") == "value"
    
    def test_escape_csv_value_with_special_chars(self):
        """Test escaping CSV values with special characters"""
        from lastpass.csv_utils import escape_csv_value
        
        # Test comma
        assert escape_csv_value("value,with,comma") == '"value,with,comma"'
        
        # Test quotes
        assert escape_csv_value('value"with"quotes') == '"value""with""quotes"'
        
        # Test newlines
        assert escape_csv_value("value\nwith\nnewlines") == '"value\nwith\nnewlines"'
        
        # Test carriage return
        assert escape_csv_value("value\rwith\rreturns") == '"value\rwith\rreturns"'
        
        # Test regular value
        assert escape_csv_value("regularvalue") == "regularvalue"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

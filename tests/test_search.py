"""
Tests for enhanced client search capabilities
"""

import pytest
import re
from lastpass import LastPassClient
from lastpass.models import Account
from lastpass.exceptions import LastPassException


class TestRegexSearch:
    """Test regular expression search functionality"""
    
    def test_search_accounts_regex_basic(self, mocker):
        """Test basic regex search"""
        client = LastPassClient()
        
        # Mock accounts
        client._accounts = [
            Account(id="1", name="test@example.com", username="user1", url="https://test.com"),
            Account(id="2", name="prod@example.com", username="user2", url="https://prod.com"),
            Account(id="3", name="dev.server", username="admin", url="https://dev.com"),
        ]
        client._blob_loaded = True
        
        # Test regex search for email addresses
        results = client.search_accounts_regex(r".*@example\.com", sync=False)
        assert len(results) == 2
        assert results[0].name == "test@example.com"
        assert results[1].name == "prod@example.com"
        
    def test_search_accounts_regex_in_username(self, mocker):
        """Test regex search in username field"""
        client = LastPassClient()
        
        client._accounts = [
            Account(id="1", name="Account 1", username="admin@company.com", url="https://app1.com"),
            Account(id="2", name="Account 2", username="user@company.com", url="https://app2.com"),
            Account(id="3", name="Account 3", username="test@other.com", url="https://app3.com"),
        ]
        client._blob_loaded = True
        
        # Search for company.com emails
        results = client.search_accounts_regex(r"@company\.com$", sync=False)
        assert len(results) == 2
        
    def test_search_accounts_regex_in_url(self, mocker):
        """Test regex search in URL field"""
        client = LastPassClient()
        
        client._accounts = [
            Account(id="1", name="GitHub", username="user", url="https://github.com/repo1"),
            Account(id="2", name="GitLab", username="user", url="https://gitlab.com/repo2"),
            Account(id="3", name="Bitbucket", username="user", url="https://bitbucket.com/repo3"),
        ]
        client._blob_loaded = True
        
        # Search for GitHub/GitLab URLs
        results = client.search_accounts_regex(r"git(hub|lab)\.com", sync=False)
        assert len(results) == 2
        
    def test_search_accounts_regex_case_insensitive(self, mocker):
        """Test that regex search is case insensitive"""
        client = LastPassClient()
        
        client._accounts = [
            Account(id="1", name="GitHub Account", username="user", url="https://github.com"),
            Account(id="2", name="gitlab account", username="user", url="https://gitlab.com"),
        ]
        client._blob_loaded = True
        
        # Search should be case insensitive
        results = client.search_accounts_regex(r"GITHUB", sync=False)
        assert len(results) == 1
        assert "GitHub" in results[0].name
        
    def test_search_accounts_regex_custom_fields(self, mocker):
        """Test regex search with custom fields"""
        client = LastPassClient()
        
        client._accounts = [
            Account(id="1", name="Account", username="user", url="https://test.com"),
            Account(id="2", name="Account", username="user", url="https://prod.com"),
        ]
        client._blob_loaded = True
        
        # Search only in specific fields
        results = client.search_accounts_regex(r"test", fields=["url"], sync=False)
        assert len(results) == 1
        assert "test.com" in results[0].url
        
    def test_search_accounts_regex_invalid_pattern(self, mocker):
        """Test that invalid regex raises exception"""
        client = LastPassClient()
        client._accounts = []
        client._blob_loaded = True
        
        with pytest.raises(LastPassException) as excinfo:
            client.search_accounts_regex(r"[invalid(regex", sync=False)
        
        assert "Invalid regex pattern" in str(excinfo.value)
        
    def test_search_accounts_regex_no_matches(self, mocker):
        """Test regex search with no matches"""
        client = LastPassClient()
        
        client._accounts = [
            Account(id="1", name="Account", username="user", url="https://example.com"),
        ]
        client._blob_loaded = True
        
        results = client.search_accounts_regex(r"nonexistent", sync=False)
        assert len(results) == 0


class TestFixedStringSearch:
    """Test fixed string search functionality"""
    
    def test_search_accounts_fixed_basic(self, mocker):
        """Test basic fixed string search"""
        client = LastPassClient()
        
        client._accounts = [
            Account(id="1", name="GitHub Account", username="user1", url="https://github.com"),
            Account(id="2", name="GitLab Account", username="user2", url="https://gitlab.com"),
            Account(id="3", name="Bitbucket", username="user3", url="https://bitbucket.com"),
        ]
        client._blob_loaded = True
        
        # Search for "Git" substring
        results = client.search_accounts_fixed("Git", sync=False)
        assert len(results) == 2
        assert "Git" in results[0].name
        assert "Git" in results[1].name
        
    def test_search_accounts_fixed_case_insensitive(self, mocker):
        """Test that fixed string search is case insensitive"""
        client = LastPassClient()
        
        client._accounts = [
            Account(id="1", name="GitHub", username="user", url="https://github.com"),
            Account(id="2", name="gitlab", username="user", url="https://gitlab.com"),
        ]
        client._blob_loaded = True
        
        # Search with different case
        results = client.search_accounts_fixed("github", sync=False)
        assert len(results) == 1
        
        results = client.search_accounts_fixed("GITHUB", sync=False)
        assert len(results) == 1
        
    def test_search_accounts_fixed_in_multiple_fields(self, mocker):
        """Test fixed string search across multiple fields"""
        client = LastPassClient()
        
        client._accounts = [
            Account(id="1", name="Production Server", username="admin", url="https://prod.com"),
            Account(id="2", name="Database", username="prod_user", url="https://db.com"),
            Account(id="3", name="Test Server", username="test", url="https://prod-server.com"),
        ]
        client._blob_loaded = True
        
        # "prod" appears in different fields
        results = client.search_accounts_fixed("prod", sync=False)
        assert len(results) == 3
        
    def test_search_accounts_fixed_custom_fields(self, mocker):
        """Test fixed string search with custom field selection"""
        client = LastPassClient()
        
        client._accounts = [
            Account(id="1", name="Account", username="github_user", url="https://example.com"),
            Account(id="2", name="GitHub Account", username="user", url="https://test.com"),
        ]
        client._blob_loaded = True
        
        # Search only in username field
        results = client.search_accounts_fixed("github", fields=["username"], sync=False)
        assert len(results) == 1
        assert "github_user" in results[0].username
        
    def test_search_accounts_fixed_no_matches(self, mocker):
        """Test fixed string search with no matches"""
        client = LastPassClient()
        
        client._accounts = [
            Account(id="1", name="Account", username="user", url="https://example.com"),
        ]
        client._blob_loaded = True
        
        results = client.search_accounts_fixed("nonexistent", sync=False)
        assert len(results) == 0
        
    def test_search_accounts_fixed_special_characters(self, mocker):
        """Test fixed string search with special characters"""
        client = LastPassClient()
        
        client._accounts = [
            Account(id="1", name="Account [prod]", username="user", url="https://example.com"),
            Account(id="2", name="Account (test)", username="user", url="https://test.com"),
        ]
        client._blob_loaded = True
        
        # Search for literal brackets (not regex)
        results = client.search_accounts_fixed("[prod]", sync=False)
        assert len(results) == 1
        assert "[prod]" in results[0].name
        
    def test_search_accounts_fixed_empty_string(self, mocker):
        """Test fixed string search with empty string"""
        client = LastPassClient()
        
        client._accounts = [
            Account(id="1", name="Account", username="user", url="https://example.com"),
        ]
        client._blob_loaded = True
        
        # Empty string should match nothing
        results = client.search_accounts_fixed("", sync=False)
        assert len(results) == 0


class TestSearchFieldSelection:
    """Test field selection in searches"""
    
    def test_default_fields_include_common_fields(self, mocker):
        """Test that default search includes common fields"""
        client = LastPassClient()
        
        client._accounts = [
            Account(id="1", name="Test", username="user", url="https://example.com", notes="important"),
            Account(id="2", name="Other", username="admin", url="https://other.com", notes="normal"),
        ]
        client._blob_loaded = True
        
        # "important" only in notes, should be found with default fields
        results = client.search_accounts_fixed("important", sync=False)
        assert len(results) == 1
        
    def test_search_specific_field_only(self, mocker):
        """Test searching in only one specific field"""
        client = LastPassClient()
        
        client._accounts = [
            Account(id="1", name="GitHub", username="user", url="https://github.com"),
            Account(id="2", name="Account", username="github_user", url="https://example.com"),
        ]
        client._blob_loaded = True
        
        # Search only in name
        results = client.search_accounts_fixed("github", fields=["name"], sync=False)
        assert len(results) == 1
        assert results[0].name == "GitHub"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

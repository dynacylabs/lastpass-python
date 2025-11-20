"""
CSV import/export utilities for LastPass
"""

import csv
import io
from typing import List, Dict, Any, Optional, TextIO
from .models import Account, Field


def escape_csv_value(value: str) -> str:
    """Escape value for CSV output"""
    if value is None:
        return ""
    
    value = str(value)
    
    # Check if we need quoting
    needs_quote = any(c in value for c in ['"', ',', '\n', '\r'])
    
    if needs_quote:
        # Escape quotes by doubling them
        value = value.replace('"', '""')
        return f'"{value}"'
    
    return value


def export_accounts_to_csv(accounts: List[Account], 
                           fields: Optional[List[str]] = None,
                           output: Optional[TextIO] = None) -> str:
    """
    Export accounts to CSV format
    
    Args:
        accounts: List of accounts to export
        fields: List of field names to include (default: all)
        output: Optional file object to write to
    
    Returns:
        CSV string if output is None
    """
    # Default fields to export
    if fields is None:
        fields = [
            "url", "username", "password", "extra", "name", "grouping", 
            "fav", "id", "attachpresent", "last_touch", "last_modified"
        ]
    
    # Create string buffer if no output file
    if output is None:
        output = io.StringIO()
        return_string = True
    else:
        return_string = False
    
    writer = csv.writer(output, lineterminator='\r\n')
    
    # Write header
    writer.writerow(fields)
    
    # Write accounts
    for account in accounts:
        row = []
        for field_name in fields:
            if field_name == "url":
                row.append(account.url)
            elif field_name == "username":
                row.append(account.username)
            elif field_name == "password":
                row.append(account.password)
            elif field_name == "extra":
                row.append(account.notes)
            elif field_name == "name":
                row.append(account.name)
            elif field_name == "grouping":
                row.append(account.group)
            elif field_name == "fav":
                row.append("1" if account.favorite else "0")
            elif field_name == "id":
                row.append(account.id)
            elif field_name == "attachpresent":
                row.append("1" if account.attach_present else "0")
            elif field_name == "last_touch":
                row.append(account.last_touch)
            elif field_name == "last_modified":
                row.append(account.last_modified_gmt)
            elif field_name == "fullname":
                row.append(account.fullname)
            else:
                # Check custom fields
                custom_field = account.get_field(field_name)
                if custom_field:
                    row.append(custom_field.value)
                else:
                    row.append("")
        
        writer.writerow(row)
    
    if return_string:
        return output.getvalue()
    
    return ""


def import_accounts_from_csv(csv_data: str, 
                             keep_duplicates: bool = False) -> List[Dict[str, Any]]:
    """
    Import accounts from CSV format
    
    Args:
        csv_data: CSV string or file content
        keep_duplicates: Keep duplicate entries instead of skipping
    
    Returns:
        List of account dictionaries ready for adding to vault
    """
    reader = csv.DictReader(io.StringIO(csv_data))
    accounts = []
    seen_names = set()
    
    for row in reader:
        # Extract account data from CSV row
        name = row.get("name", "")
        username = row.get("username", "")
        password = row.get("password", "")
        url = row.get("url", "")
        notes = row.get("extra", "")
        group = row.get("grouping", "")
        
        # Skip if duplicate and not keeping duplicates
        if not keep_duplicates:
            # Create unique identifier from name and username
            identifier = f"{group}/{name}:{username}"
            if identifier in seen_names:
                continue
            seen_names.add(identifier)
        
        # Build account dict
        account_data = {
            "name": name,
            "username": username,
            "password": password,
            "url": url,
            "notes": notes,
            "group": group,
        }
        
        # Handle optional fields
        if "fav" in row:
            account_data["favorite"] = row["fav"] == "1"
        
        # Extract custom fields (any column not in standard fields)
        standard_fields = {
            "url", "username", "password", "extra", "name", "grouping",
            "fav", "id", "attachpresent", "last_touch", "last_modified", "fullname"
        }
        
        custom_fields = {}
        for key, value in row.items():
            if key not in standard_fields and value:
                custom_fields[key] = value
        
        if custom_fields:
            account_data["fields"] = custom_fields
        
        accounts.append(account_data)
    
    return accounts


def parse_csv_field_list(field_str: str) -> List[str]:
    """Parse comma-separated field list"""
    if not field_str:
        return None
    
    return [f.strip() for f in field_str.split(",") if f.strip()]

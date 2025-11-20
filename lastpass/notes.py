"""
Notes expansion and collapse for structured secure notes

This module handles the conversion between LastPass secure note format
(key:value pairs in notes field) and expanded Account objects with 
separate fields for easier manipulation.
"""

from typing import Optional
from copy import deepcopy

from .models import Account, Field
from .note_types import get_note_type_by_name, has_field, is_multiline_field


def is_secure_note(account: Account) -> bool:
    """
    Check if account is a secure note
    
    Args:
        account: Account to check
    
    Returns:
        True if account is a secure note
    """
    return account.url == "http://sn"


def notes_expand(account: Account) -> Optional[Account]:
    """
    Expand secure note into separate fields
    
    Secure notes store structured data in the notes field as key:value pairs.
    This function parses that format and returns a new Account with the data
    expanded into separate username, password, url, and custom fields.
    
    Args:
        account: Account with secure note data
    
    Returns:
        New Account with expanded fields, or None if not a secure note
    """
    if not is_secure_note(account):
        return None
    
    # Check for NoteType header
    if not account.notes.startswith("NoteType:"):
        return None
    
    # Create expanded account
    expanded = Account(
        id=account.id,
        name=account.name,
        group=account.group,
        fullname=account.fullname,
        url="",
        username="",
        password="",
        notes="",
        share=account.share,
        pwprotect=account.pwprotect,
        fields=[],
        attachments=account.attachments.copy() if account.attachments else [],
        attachkey=account.attachkey,
        attach_present=account.attach_present,
    )
    
    # Parse note type
    note_type = None
    lines = account.notes.split('\n')
    if lines:
        first_line = lines[0]
        if first_line.startswith("NoteType:"):
            type_name = first_line[9:].strip()
            note_type = get_note_type_by_name(type_name)
    
    # Parse fields
    current_field = None
    notes_section_started = False
    
    for i, line in enumerate(lines):
        if not line and not current_field:
            continue
        
        # Check if this is the Notes: section (rest of file is notes)
        if line.startswith("Notes:"):
            notes_value = line[6:].strip()
            # Rest of content after "Notes:" goes into notes
            remaining_lines = lines[i+1:]
            if remaining_lines:
                if notes_value:
                    expanded.notes = notes_value + '\n' + '\n'.join(remaining_lines)
                else:
                    expanded.notes = '\n'.join(remaining_lines)
            else:
                expanded.notes = notes_value
            # Remove trailing newline
            expanded.notes = expanded.notes.rstrip('\n')
            notes_section_started = True
            break
        
        # Parse key:value line
        if ':' in line:
            colon_idx = line.index(':')
            key = line[:colon_idx]
            value = line[colon_idx+1:].strip()
            
            # Check if this key belongs to a known note type field
            if note_type and current_field:
                # Check if this is a new field or continuation
                if not has_field(note_type, key) and is_multiline_field(note_type, current_field.name):
                    # This is a continuation line (like Proc-Type in SSH keys)
                    current_field.value += '\n' + line
                    continue
            
            # Handle special fields
            if key == "Username":
                expanded.username = value
                current_field = None
            elif key == "Password":
                expanded.password = value
                current_field = None
            elif key == "URL":
                expanded.url = value
                current_field = None
            elif key == "NoteType":
                # Store as field for roundtrip
                new_field = Field(name=key, value=value, type="text")
                expanded.fields.append(new_field)
                current_field = None
            else:
                # Custom field
                new_field = Field(name=key, value=value, type="text")
                expanded.fields.append(new_field)
                current_field = new_field
        else:
            # Continuation line (no colon)
            if current_field:
                # Append to current field's value
                current_field.value += '\n' + line
    
    # If no fields were parsed, return original notes
    if (not expanded.username and not expanded.password and 
        not expanded.url and not expanded.notes and not expanded.fields):
        expanded.notes = account.notes
    
    # Ensure empty strings for unset fields
    if not expanded.notes:
        expanded.notes = ""
    if not expanded.url:
        expanded.url = ""
    if not expanded.username:
        expanded.username = ""
    if not expanded.password:
        expanded.password = ""
    
    return expanded


def notes_collapse(account: Account) -> Account:
    """
    Collapse account fields back into secure note format
    
    Takes an account with separate fields and converts it back to the
    secure note format with key:value pairs in the notes field.
    
    Args:
        account: Account with expanded fields
    
    Returns:
        New Account in secure note format
    """
    # Create collapsed account
    collapsed = Account(
        id=account.id,
        name=account.name,
        group=account.group,
        fullname=account.fullname,
        url="http://sn",
        username="",
        password="",
        notes="",
        share=account.share,
        pwprotect=account.pwprotect,
        fields=[],
        attachments=account.attachments.copy() if account.attachments else [],
        attachkey=account.attachkey,
        attach_present=account.attach_present,
    )
    
    # Build notes content
    note_lines = []
    
    # NoteType must be first if present
    for field in account.fields:
        if field.name == "NoteType":
            note_lines.append(f"{field.name.strip()}:{field.value.strip()}")
            break
    
    # Add other fields
    for field in account.fields:
        if field.name != "NoteType":
            note_lines.append(f"{field.name.strip()}:{field.value.strip()}")
    
    # Add special fields if present
    if account.username and account.username.strip():
        note_lines.append(f"Username:{account.username.strip()}")
    
    if account.password and account.password.strip():
        note_lines.append(f"Password:{account.password.strip()}")
    
    if account.url and account.url.strip() and account.url != "http://sn":
        note_lines.append(f"URL:{account.url.strip()}")
    
    if account.notes and account.notes.strip():
        note_lines.append(f"Notes:{account.notes.strip()}")
    
    collapsed.notes = '\n'.join(note_lines)
    
    return collapsed

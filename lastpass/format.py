"""
Printf-style formatting for LastPass accounts and fields

Supports C CLI format codes:
  %ai - account id
  %an - account name
  %aN - account name with path (fullname)
  %au - account username
  %ap - account password
  %am - account modification time
  %aU - account last touch time
  %as - account share name
  %ag - account group name
  %al - account URL
  %fn - field name
  %fv - field value
  
Special modifiers:
  %/ - add trailing slash only if value is non-empty
  %% - literal percent sign
"""

from typing import Optional, Tuple
from datetime import datetime
from .models import Account


def format_timestamp(timestamp: Optional[str], utc: bool = True) -> str:
    """
    Format a timestamp string to human-readable format
    
    Args:
        timestamp: Unix timestamp as string
        utc: Use UTC time (True) or local time (False)
    
    Returns:
        Formatted timestamp string (YYYY-MM-DD HH:MM) or empty string
    """
    if not timestamp:
        return ""
    
    try:
        ts = int(timestamp)
        if ts == 0:
            return ""
        
        dt = datetime.utcfromtimestamp(ts) if utc else datetime.fromtimestamp(ts)
        return dt.strftime("%Y-%m-%d %H:%M")
    except (ValueError, OSError):
        return ""


def get_display_fullname(account: Account) -> str:
    """
    Get display fullname with (none) prefix if no group/share
    
    Args:
        account: Account object
    
    Returns:
        Display fullname
    """
    if account.share or account.group:
        return account.fullname
    else:
        return f"(none)/{account.fullname}"


def format_account_field(code: str, account: Account, add_slash: bool = False) -> str:
    """
    Format a single account field based on format code
    
    Args:
        code: Format code (single character)
        account: Account object
        add_slash: Add trailing slash if value is non-empty
    
    Returns:
        Formatted field value
    """
    value = ""
    
    if code == 'i':
        # account id
        value = account.id or ""
    elif code == 'n':
        # account name (shortname)
        value = account.name or ""
    elif code == 'N':
        # account fullname (with path)
        value = get_display_fullname(account)
    elif code == 'u':
        # account username
        value = account.username or ""
    elif code == 'p':
        # account password
        value = account.password or ""
    elif code == 'm':
        # modification time
        value = format_timestamp(getattr(account, 'last_modified', None), utc=True)
    elif code == 'U':
        # last touch time
        value = format_timestamp(getattr(account, 'last_touch', None), utc=False)
    elif code == 's':
        # share name
        value = account.share.name if account.share else ""
    elif code == 'g':
        # group name
        value = account.group or ""
    elif code == 'l':
        # URL
        value = account.url or ""
    
    # Add trailing slash if requested and value is non-empty
    if value and add_slash:
        value += "/"
    
    return value


def format_field_field(code: str, field_name: Optional[str], 
                       field_value: Optional[str], add_slash: bool = False) -> str:
    """
    Format a single field name or value based on format code
    
    Args:
        code: Format code (single character)
        field_name: Field name
        field_value: Field value
        add_slash: Add trailing slash if value is non-empty
    
    Returns:
        Formatted value
    """
    value = ""
    
    if code == 'n' and field_name:
        value = field_name
    elif code == 'v' and field_value:
        value = field_value
    
    # Add trailing slash if requested and value is non-empty
    if value and add_slash:
        value += "/"
    
    return value


def format_account(format_str: str, account: Account, 
                   field_name: Optional[str] = None,
                   field_value: Optional[str] = None) -> str:
    """
    Format an account using printf-style format string
    
    Format codes:
      %ai - account id
      %an - account name
      %aN - account fullname with path
      %au - account username
      %ap - account password
      %am - account modification time
      %aU - account last touch time
      %as - account share name
      %ag - account group name
      %al - account URL
      %fn - field name (if provided)
      %fv - field value (if provided)
      %/ - add trailing slash (modifier, use before code)
      %% - literal percent
    
    Examples:
      "%/as%/ag%an" -> "ShareName/GroupName/AccountName"
      "%au: %ap" -> "username: password"
      "ID: %ai" -> "ID: 12345"
    
    Args:
        format_str: Format string with % codes
        account: Account object to format
        field_name: Optional field name for %fn
        field_value: Optional field value for %fv
    
    Returns:
        Formatted string
    """
    result = []
    i = 0
    
    while i < len(format_str):
        if format_str[i] != '%':
            result.append(format_str[i])
            i += 1
            continue
        
        # Found %, check next character
        if i + 1 >= len(format_str):
            # Trailing %, just add it
            result.append('%')
            i += 1
            continue
        
        next_char = format_str[i + 1]
        
        if next_char == '%':
            # %% -> literal %
            result.append('%')
            i += 2
            continue
        
        # Check for slash modifier
        add_slash = False
        if next_char == '/':
            add_slash = True
            i += 2
            if i >= len(format_str):
                # Trailing %/, just add it
                result.append('%/')
                break
            next_char = format_str[i]
        else:
            i += 1
        
        # Check for format code
        if i >= len(format_str):
            # No code after %, add the %
            result.append('%')
            if add_slash:
                result.append('/')
            break
        
        code_char = format_str[i]
        i += 1
        
        # Check if it's an account format (a) or field format (f)
        if code_char == 'a':
            # Account field
            if i >= len(format_str):
                # No field specifier, add literal
                result.append('%')
                if add_slash:
                    result.append('/')
                result.append('a')
                break
            
            field_code = format_str[i]
            i += 1
            value = format_account_field(field_code, account, add_slash)
            result.append(value)
        
        elif code_char == 'f':
            # Field name/value
            if i >= len(format_str):
                # No field specifier, add literal
                result.append('%')
                if add_slash:
                    result.append('/')
                result.append('f')
                break
            
            field_code = format_str[i]
            i += 1
            value = format_field_field(field_code, field_name, field_value, add_slash)
            result.append(value)
        
        else:
            # Unknown format code, add it literally
            result.append('%')
            if add_slash:
                result.append('/')
            result.append(code_char)
    
    return ''.join(result)


def format_accounts(format_str: str, accounts: list) -> list:
    """
    Format multiple accounts using format string
    
    Args:
        format_str: Format string
        accounts: List of Account objects
    
    Returns:
        List of formatted strings
    """
    return [format_account(format_str, account) for account in accounts]

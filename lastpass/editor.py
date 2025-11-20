"""
External editor integration for multi-line editing
"""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional


class Editor:
    """External editor integration"""
    
    @staticmethod
    def _get_editor() -> str:
        """Get editor command"""
        # Check environment variables in order of preference
        for var in ['VISUAL', 'EDITOR']:
            editor = os.environ.get(var)
            if editor:
                return editor
        
        # Default editors
        for editor in ['vi', 'vim', 'nano', 'emacs']:
            if subprocess.run(['which', editor], 
                            capture_output=True, 
                            check=False).returncode == 0:
                return editor
        
        return 'vi'
    
    @staticmethod
    def _get_secure_tmpdir() -> Path:
        """Get secure temporary directory"""
        # Check for secure tmpdir first
        secure_tmpdir = os.environ.get('SECURE_TMPDIR')
        if secure_tmpdir:
            tmpdir = Path(secure_tmpdir)
            if tmpdir.exists():
                return tmpdir
        
        # Fall back to TMPDIR or /tmp
        tmpdir_env = os.environ.get('TMPDIR', '/tmp')
        return Path(tmpdir_env)
    
    @staticmethod
    def edit_text(initial_text: str = "", 
                  prefix: str = "lpass-",
                  suffix: str = ".txt") -> Optional[str]:
        """
        Edit text in external editor
        
        Args:
            initial_text: Initial text content
            prefix: Temporary file prefix
            suffix: Temporary file suffix
        
        Returns:
            Edited text or None if cancelled
        """
        tmpdir = Editor._get_secure_tmpdir()
        
        # Create secure temporary file
        fd, tmppath = tempfile.mkstemp(
            prefix=prefix,
            suffix=suffix,
            dir=tmpdir,
            text=True
        )
        
        try:
            # Set secure permissions
            os.chmod(tmppath, 0o600)
            
            # Write initial content
            with os.fdopen(fd, 'w') as f:
                f.write(initial_text)
            
            # Get editor
            editor = Editor._get_editor()
            
            # Launch editor
            result = subprocess.run(
                [editor, tmppath],
                check=False
            )
            
            if result.returncode != 0:
                return None
            
            # Read edited content
            with open(tmppath, 'r') as f:
                edited_text = f.read()
            
            # Check if modified
            if edited_text == initial_text:
                return None
            
            return edited_text
        
        finally:
            # Clean up temporary file
            try:
                os.unlink(tmppath)
            except Exception:
                pass
    
    @staticmethod
    def edit_field(field_name: str, current_value: str = "") -> Optional[str]:
        """
        Edit a field value in external editor
        
        Args:
            field_name: Name of field being edited
            current_value: Current field value
        
        Returns:
            New value or None if cancelled
        """
        # Add header comment
        header = f"# Edit {field_name}\n# Lines starting with # will be ignored\n\n"
        initial_text = header + current_value
        
        edited = Editor.edit_text(
            initial_text,
            prefix=f"lpass-{field_name}-",
            suffix=".txt"
        )
        
        if edited is None:
            return None
        
        # Remove header and comment lines
        lines = []
        for line in edited.splitlines():
            if not line.startswith('#'):
                lines.append(line)
        
        return '\n'.join(lines)
    
    @staticmethod
    def edit_account_template(account_data: dict) -> Optional[dict]:
        """
        Edit complete account in external editor with template
        
        Args:
            account_data: Dict with account fields (name, username, password, url, notes, fields, etc.)
        
        Returns:
            Dict with edited account data or None if cancelled
        """
        # Create template
        lines = []
        
        # Required fields
        lines.append(f"Name: {account_data.get('name', '')}")
        
        # Check if it's a secure note (has NoteType field)
        is_secure_note = any(
            f.get('name') == 'NoteType' 
            for f in account_data.get('fields', [])
        )
        
        if not is_secure_note:
            # Standard account fields
            lines.append(f"URL: {account_data.get('url', '')}")
            lines.append(f"Username: {account_data.get('username', '')}")
            lines.append(f"Password: {account_data.get('password', '')}")
        
        # Additional fields
        for field in account_data.get('fields', []):
            field_name = field.get('name', '')
            field_value = field.get('value', '')
            if field_name and field_name != 'NoteType':
                lines.append(f"{field_name}: {field_value}")
        
        # Notes section
        lines.append("Notes:    # Add notes below this line.")
        lines.append(account_data.get('notes', ''))
        
        template = '\n'.join(lines)
        
        # Edit in external editor
        edited = Editor.edit_text(
            template,
            prefix="lpass-account-",
            suffix=".txt"
        )
        
        if edited is None:
            return None
        
        # Parse edited content
        return Editor._parse_account_template(edited, is_secure_note)
    
    @staticmethod
    def _parse_account_template(content: str, is_secure_note: bool = False) -> dict:
        """
        Parse account template back into dict
        
        Args:
            content: Edited template content
            is_secure_note: Whether this is a secure note
        
        Returns:
            Dict with parsed account data
        """
        result = {
            'name': '',
            'username': '',
            'password': '',
            'url': '',
            'notes': '',
            'fields': []
        }
        
        lines = content.splitlines()
        current_field = None
        current_value = []
        in_notes = False
        notes_lines = []
        
        for line in lines:
            # Skip comment lines in notes
            if in_notes:
                if not line.strip().startswith('#'):
                    notes_lines.append(line)
                continue
            
            # Check for field: value format
            if ':' in line:
                colon_idx = line.index(':')
                field_name = line[:colon_idx].strip()
                field_value = line[colon_idx + 1:].strip()
                
                # Save previous field if any
                if current_field:
                    value = '\n'.join(current_value)
                    if current_field == 'Name':
                        result['name'] = value
                    elif current_field == 'URL':
                        result['url'] = value
                    elif current_field == 'Username':
                        result['username'] = value
                    elif current_field == 'Password':
                        result['password'] = value
                    else:
                        # Custom field
                        result['fields'].append({
                            'name': current_field,
                            'value': value,
                            'type': 'text'
                        })
                
                # Start new field
                if field_name == 'Notes':
                    in_notes = True
                    # Remove comment from notes line
                    if '#' in field_value:
                        field_value = field_value[:field_value.index('#')].strip()
                    if field_value:
                        notes_lines.append(field_value)
                else:
                    current_field = field_name
                    current_value = [field_value] if field_value else []
            else:
                # Continuation of current field
                if current_field and not in_notes:
                    current_value.append(line)
        
        # Save last field
        if current_field and not in_notes:
            value = '\n'.join(current_value)
            if current_field == 'Name':
                result['name'] = value
            elif current_field == 'URL':
                result['url'] = value
            elif current_field == 'Username':
                result['username'] = value
            elif current_field == 'Password':
                result['password'] = value
            else:
                result['fields'].append({
                    'name': current_field,
                    'value': value,
                    'type': 'text'
                })
        
        # Save notes
        result['notes'] = '\n'.join(notes_lines)
        
        return result
    
    @staticmethod
    def edit_notes(current_notes: str = "") -> Optional[str]:
        """
        Edit account notes in external editor
        
        Args:
            current_notes: Current notes content
        
        Returns:
            New notes or None if cancelled
        """
        return Editor.edit_field("Notes", current_notes)

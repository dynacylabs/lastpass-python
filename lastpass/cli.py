"""
Command-line interface for LastPass
"""

import sys
import argparse
import json
import getpass
import re
from typing import Optional, List
from pathlib import Path

from . import __version__
from .client import LastPassClient
from .exceptions import LastPassException, AccountNotFoundException
from .models import Account
from .note_types import NoteType, get_note_type_by_shortname, NOTE_TEMPLATES
from .csv_utils import parse_csv_field_list
from .clipboard import ClipboardManager
from .terminal import Terminal, ColorMode
from .config import Config


class CLI:
    """Command-line interface handler"""
    
    def __init__(self):
        self.client = LastPassClient()
        self.config = Config()
        self.clipboard_timeout = ClipboardManager.get_clipboard_timeout()
    
    def _should_sync(self, sync_mode: str) -> bool:
        """
        Determine if sync should be performed based on sync mode
        
        Args:
            sync_mode: 'auto', 'now', or 'no'
        
        Returns:
            True if sync should be performed
        """
        if sync_mode == 'no':
            return False
        elif sync_mode == 'now':
            return True
        else:  # auto
            # For auto mode, we sync for write operations
            # Read operations will use cached data if recent
            return True
    
    def run(self, args: Optional[List[str]] = None) -> int:
        """Run CLI with arguments"""
        parser = self._create_parser()
        
        if args is None:
            args = sys.argv[1:]
        
        # Expand aliases
        args = self.config.expand_alias(args)
        
        # If no args, show help
        if not args:
            parser.print_help()
            return 1
        
        parsed_args = parser.parse_args(args)
        
        try:
            return parsed_args.func(parsed_args)
        except LastPassException as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
        except KeyboardInterrupt:
            print("\nAborted", file=sys.stderr)
            return 130
        except Exception as e:
            print(f"Unexpected error: {e}", file=sys.stderr)
            return 1
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create argument parser"""
        parser = argparse.ArgumentParser(
            prog='lpass',
            description='LastPass command-line interface',
        )
        
        parser.add_argument('--version', action='version', 
                          version=f'LastPass CLI v{__version__}')
        
        subparsers = parser.add_subparsers(dest='command', help='Commands')
        
        # Login
        login_parser = subparsers.add_parser('login', help='Login to LastPass')
        login_parser.add_argument('username', help='LastPass username/email')
        login_parser.add_argument('--trust', action='store_true',
                                help='Trust this device')
        login_parser.add_argument('--otp', help='One-time password for 2FA')
        login_parser.add_argument('--force', '-f', action='store_true',
                                help='Force new login')
        login_parser.add_argument('--plaintext-key', action='store_true',
                                help='Store decryption key in plaintext (less secure)')
        login_parser.add_argument('--color', choices=['auto', 'never', 'always'],
                                default='auto', help='Color output mode')
        login_parser.set_defaults(func=self.cmd_login)
        
        # Logout
        logout_parser = subparsers.add_parser('logout', help='Logout from LastPass')
        logout_parser.add_argument('--force', '-f', action='store_true',
                                 help='Force logout')
        logout_parser.add_argument('--color', choices=['auto', 'never', 'always'],
                                 default='auto', help='Color output mode')
        logout_parser.set_defaults(func=self.cmd_logout)
        
        # Status
        status_parser = subparsers.add_parser('status', help='Show login status')
        status_parser.add_argument('--quiet', '-q', action='store_true',
                                 help='Quiet mode')
        status_parser.add_argument('--color', choices=['auto', 'never', 'always'],
                                 default='auto', help='Color output mode')
        status_parser.set_defaults(func=self.cmd_status)
        
        # Show
        show_parser = subparsers.add_parser('show', help='Show account details')
        show_parser.add_argument('query', help='Account name, ID, or URL')
        show_parser.add_argument('--password', action='store_true',
                               help='Show only password')
        show_parser.add_argument('--username', action='store_true',
                               help='Show only username')
        show_parser.add_argument('--url', action='store_true',
                               help='Show only URL')
        show_parser.add_argument('--notes', action='store_true',
                               help='Show only notes')
        show_parser.add_argument('--id', action='store_true',
                               help='Show only account ID')
        show_parser.add_argument('--name', action='store_true',
                               help='Show only account name')
        show_parser.add_argument('--field', metavar='FIELD',
                               help='Show only specified field')
        show_parser.add_argument('--attach', metavar='ATTACHID',
                               help='Download and display attachment')
        show_parser.add_argument('--all', action='store_true',
                               help='Show all account details')
        show_parser.add_argument('--json', '-j', action='store_true',
                               help='Output as JSON')
        show_parser.add_argument('--clip', '-c', action='store_true',
                               help='Copy to clipboard')
        show_parser.add_argument('--expand-multi', '-x', action='store_true',
                               help='Expand multi-line fields')
        show_parser.add_argument('--basic-regexp', '-G', action='store_true',
                               help='Use basic regular expression for query')
        show_parser.add_argument('--fixed-strings', '-F', action='store_true',
                               help='Use fixed string search (no regex)')
        show_parser.add_argument('--quiet', '-q', action='store_true',
                               help='Suppress non-essential output')
        show_parser.add_argument('--format', metavar='FMT',
                               help='Custom field format string')
        show_parser.add_argument('--title-format', metavar='FMT',
                               help='Custom title format string')
        show_parser.add_argument('--sync', choices=['auto', 'now', 'no'],
                               default='auto', help='Sync mode')
        show_parser.add_argument('--color', choices=['auto', 'never', 'always'],
                               default='auto', help='Color output mode')
        show_parser.set_defaults(func=self.cmd_show)
        
        # List
        ls_parser = subparsers.add_parser('ls', help='List accounts')
        ls_parser.add_argument('group', nargs='?', help='Filter by group')
        ls_parser.add_argument('--long', '-l', action='store_true',
                             help='Long listing format')
        ls_parser.add_argument('--json', '-j', action='store_true',
                             help='Output as JSON')
        ls_parser.add_argument('-m', action='store_true',
                             help='Show last modified time')
        ls_parser.add_argument('-u', action='store_true',
                             help='Show username in listing')
        ls_parser.add_argument('--format', metavar='FMT',
                             help='Custom output format string')
        ls_parser.add_argument('--sync', choices=['auto', 'now', 'no'],
                             default='auto', help='Sync mode')
        ls_parser.add_argument('--color', choices=['auto', 'never', 'always'],
                             default='auto', help='Color output mode')
        ls_parser.set_defaults(func=self.cmd_ls)
        
        # Generate
        generate_parser = subparsers.add_parser('generate', 
                                               help='Generate password')
        generate_parser.add_argument('name', nargs='?', help='Account name (optional, for creating account)')
        generate_parser.add_argument('length', type=int, nargs='?', default=16,
                                   help='Password length (default: 16)')
        generate_parser.add_argument('--username', metavar='USERNAME',
                                   help='Username for new account')
        generate_parser.add_argument('--url', metavar='URL',
                                   help='URL for new account')
        generate_parser.add_argument('--no-symbols', action='store_true',
                                   help='Exclude symbols')
        generate_parser.add_argument('--clip', '-c', action='store_true',
                                   help='Copy to clipboard')
        generate_parser.add_argument('--sync', choices=['auto', 'now', 'no'],
                                   default='auto', help='Sync mode')
        generate_parser.set_defaults(func=self.cmd_generate)
        
        # Sync
        sync_parser = subparsers.add_parser('sync', help='Sync vault from server')
        sync_parser.add_argument('--background', '-b', action='store_true',
                               help='Run sync in background')
        sync_parser.add_argument('--color', choices=['auto', 'never', 'always'],
                               default='auto', help='Color output mode')
        sync_parser.set_defaults(func=self.cmd_sync)
        
        # Add
        add_parser = subparsers.add_parser('add', help='Add new account')
        add_parser.add_argument('name', help='Account name')
        add_parser.add_argument('--username', default='', help='Username')
        add_parser.add_argument('--password', default='', help='Password (leave empty to prompt)')
        add_parser.add_argument('--url', default='', help='Website URL')
        add_parser.add_argument('--notes', default='', help='Notes')
        add_parser.add_argument('--group', default='', help='Group/folder name')
        add_parser.add_argument('--generate', type=int, metavar='LENGTH',
                              help='Generate password of specified length')
        add_parser.add_argument('--note-type', help='Secure note type (e.g., creditcard, sshkey, server)')
        add_parser.add_argument('--app', action='store_true',
                              help='Create application entry')
        add_parser.add_argument('--non-interactive', action='store_true',
                              help='Non-interactive mode (read from stdin)')
        add_parser.add_argument('--sync', choices=['auto', 'now', 'no'],
                              default='auto', help='Sync mode')
        add_parser.add_argument('--color', choices=['auto', 'never', 'always'],
                              default='auto', help='Color output mode')
        add_parser.set_defaults(func=self.cmd_add)
        
        # Edit
        edit_parser = subparsers.add_parser('edit', help='Edit existing account')
        edit_parser.add_argument('query', help='Account name, ID, or URL')
        edit_parser.add_argument('--name', help='New name')
        edit_parser.add_argument('--username', help='New username')
        edit_parser.add_argument('--password', help='New password (leave empty to prompt)')
        edit_parser.add_argument('--url', help='New URL')
        edit_parser.add_argument('--notes', help='New notes')
        edit_parser.add_argument('--group', help='New group/folder')
        edit_parser.add_argument('--upload-attachment', metavar='FILEPATH',
                              help='Upload file as attachment')
        edit_parser.add_argument('--non-interactive', action='store_true',
                              help='Non-interactive mode (read from stdin)')
        edit_parser.add_argument('--sync', choices=['auto', 'now', 'no'],
                              default='auto', help='Sync mode')
        edit_parser.set_defaults(func=self.cmd_edit)
        
        # Remove
        rm_parser = subparsers.add_parser('rm', help='Remove account')
        rm_parser.add_argument('query', help='Account name, ID, or URL')
        rm_parser.add_argument('--force', '-f', action='store_true',
                             help='Skip confirmation')
        rm_parser.add_argument('--sync', choices=['auto', 'now', 'no'],
                             default='auto', help='Sync mode')
        rm_parser.set_defaults(func=self.cmd_rm)
        
        # Duplicate
        duplicate_parser = subparsers.add_parser('duplicate', help='Duplicate account')
        duplicate_parser.add_argument('query', help='Account name, ID, or URL')
        duplicate_parser.add_argument('--name', help='Name for duplicate')
        duplicate_parser.add_argument('--sync', choices=['auto', 'now', 'no'],
                                    default='auto', help='Sync mode')
        duplicate_parser.set_defaults(func=self.cmd_duplicate)
        
        # Move
        mv_parser = subparsers.add_parser('mv', help='Move account to different group')
        mv_parser.add_argument('query', help='Account name, ID, or URL')
        mv_parser.add_argument('group', help='New group/folder name')
        mv_parser.add_argument('--sync', choices=['auto', 'now', 'no'],
                             default='auto', help='Sync mode')
        mv_parser.set_defaults(func=self.cmd_mv)
        
        # Export
        export_parser = subparsers.add_parser('export', help='Export vault to CSV')
        export_parser.add_argument('--fields', help='Comma-separated list of fields to export')
        export_parser.add_argument('--output', '-o', help='Output file (default: stdout)')
        export_parser.add_argument('--sync', choices=['auto', 'now', 'no'],
                                  default='auto', help='Sync mode')
        export_parser.set_defaults(func=self.cmd_export)
        
        # Import
        import_parser = subparsers.add_parser('import', help='Import accounts from CSV')
        import_parser.add_argument('file', nargs='?', help='CSV file to import (default: stdin)')
        import_parser.add_argument('--keep-dupes', action='store_true',
                                  help='Keep duplicate entries (do not skip duplicates)')
        import_parser.add_argument('--sync', choices=['auto', 'now', 'no'],
                                  default='auto', help='Sync mode')
        import_parser.set_defaults(func=self.cmd_import)
        
        # Password change
        passwd_parser = subparsers.add_parser('passwd', help='Change master password')
        passwd_parser.set_defaults(func=self.cmd_passwd)
        
        # Share management
        share_parser = subparsers.add_parser('share', help='Manage shared folders')
        share_subparsers = share_parser.add_subparsers(dest='share_command', help='Share commands')
        
        # share create
        share_create = share_subparsers.add_parser('create', help='Create shared folder')
        share_create.add_argument('name', help='Shared folder name')
        share_create.set_defaults(func=self.cmd_share_create)
        
        # share rm
        share_rm = share_subparsers.add_parser('rm', help='Delete shared folder')
        share_rm.add_argument('name', help='Shared folder name or ID')
        share_rm.set_defaults(func=self.cmd_share_rm)
        
        # share userls
        share_userls = share_subparsers.add_parser('userls', help='List users in shared folder')
        share_userls.add_argument('name', help='Shared folder name or ID')
        share_userls.set_defaults(func=self.cmd_share_userls)
        
        # share useradd
        share_useradd = share_subparsers.add_parser('useradd', help='Add user to shared folder')
        share_useradd.add_argument('name', help='Shared folder name or ID')
        share_useradd.add_argument('username', help='Username/email to add')
        share_useradd.add_argument('--read-only', action='store_true', help='Grant read-only access')
        share_useradd.add_argument('--admin', action='store_true', help='Grant admin privileges')
        share_useradd.add_argument('--hidden', action='store_true', help='Hide passwords')
        share_useradd.set_defaults(func=self.cmd_share_useradd)
        
        # share userdel
        share_userdel = share_subparsers.add_parser('userdel', help='Remove user from shared folder')
        share_userdel.add_argument('name', help='Shared folder name or ID')
        share_userdel.add_argument('username', help='Username/email to remove')
        share_userdel.set_defaults(func=self.cmd_share_userdel)
        
        # share usermod
        share_usermod = share_subparsers.add_parser('usermod', help='Modify user permissions')
        share_usermod.add_argument('name', help='Shared folder name or ID')
        share_usermod.add_argument('username', help='Username/email to modify')
        share_usermod.add_argument('--read-only', type=lambda x: x.lower() == 'true', 
                                   help='Set read-only (true/false)')
        share_usermod.add_argument('--admin', type=lambda x: x.lower() == 'true',
                                   help='Set admin (true/false)')
        share_usermod.add_argument('--hidden', type=lambda x: x.lower() == 'true',
                                   help='Hide passwords (true/false)')
        share_usermod.set_defaults(func=self.cmd_share_usermod)
        
        # share limit
        share_limit = share_subparsers.add_parser('limit', help='Manage share access limits')
        share_limit.add_argument('name', help='Shared folder name or ID')
        share_limit.add_argument('username', help='Username/email')
        share_limit.add_argument('sites', nargs='*', help='Site IDs to allow/deny')
        share_limit.add_argument('--deny', action='store_true', help='Use deny list (default is allow list)')
        share_limit.add_argument('--allow', action='store_true', help='Use allow list (default)')
        share_limit.add_argument('--add', action='store_true', help='Add sites to limit')
        share_limit.add_argument('--rm', action='store_true', help='Remove sites from limit')
        share_limit.add_argument('--clear', action='store_true', help='Clear all limits')
        share_limit.add_argument('--show', action='store_true', help='Show current limits')
        share_limit.set_defaults(func=self.cmd_share_limit)
        
        return parser
    
    def _is_binary_attachment(self, data: bytes) -> bool:
        """
        Check if attachment data is binary
        
        Args:
            data: Attachment data
        
        Returns:
            True if binary, False if text
        """
        # Check first 100 bytes for non-printable characters
        sample_size = min(len(data), 100)
        sample = data[:sample_size]
        
        # Count non-printable characters (excluding common whitespace)
        non_printable = 0
        for byte in sample:
            if byte < 32 and byte not in (9, 10, 13):  # tab, newline, carriage return
                non_printable += 1
            elif byte >= 127:
                non_printable += 1
        
        # Consider binary if more than 10% non-printable
        return non_printable > (sample_size * 0.1)
    
    def cmd_login(self, args) -> int:
        """Handle login command"""
        # Set color mode
        Terminal.set_color_mode(Terminal.parse_color_mode(args.color))
        
        # Warn about plaintext-key
        if args.plaintext_key and not args.force:
            print(Terminal.warning(
                "WARNING: --plaintext-key will greatly reduce the security of your passwords."
            ), file=sys.stderr)
            print("You are advised to use a more secure method.", file=sys.stderr)
            response = input("Are you sure you would like to do this? [y/N]: ")
            if response.lower() not in ['y', 'yes']:
                print("Login aborted. Try again without --plaintext-key.")
                return 1
        
        password = getpass.getpass("Master Password: ")
        
        try:
            self.client.login(
                args.username,
                password,
                trust=args.trust,
                otp=args.otp,
                force=args.force
            )
            
            # Store plaintext key if requested
            if args.plaintext_key and self.client.decryption_key:
                self.config.set_plaintext_key(self.client.decryption_key)
            else:
                # Remove any existing plaintext key
                self.config.delete_plaintext_key()
            
            username_formatted = Terminal.underline(args.username)
            print(Terminal.success("Success") + f": Logged in as {username_formatted}")
            return 0
        except Exception as e:
            print(Terminal.error(f"Login failed: {e}"), file=sys.stderr)
            return 1
    
    def cmd_logout(self, args) -> int:
        """Handle logout command"""
        # Set color mode
        Terminal.set_color_mode(Terminal.parse_color_mode(args.color))
        
        try:
            self.client.logout(force=args.force)
            # Clean up plaintext key
            self.config.delete_plaintext_key()
            print("Logged out successfully")
            return 0
        except Exception as e:
            print(Terminal.error(f"Logout failed: {e}"), file=sys.stderr)
            return 1
    
    def cmd_status(self, args) -> int:
        """Handle status command"""
        # Set color mode
        Terminal.set_color_mode(Terminal.parse_color_mode(args.color))
        
        if self.client.is_logged_in():
            if not args.quiet:
                username = Terminal.bold(self.client.session.uid)
                print(f"Logged in as {username}")
            return 0
        else:
            if not args.quiet:
                print("Not logged in")
            return 1
    
    def cmd_show(self, args) -> int:
        """Handle show command"""
        # Set color mode
        Terminal.set_color_mode(Terminal.parse_color_mode(args.color))
        
        # Handle sync option
        sync_mode = self._should_sync(args.sync)
        
        try:
            # Handle attachment display
            if args.attach:
                account = self.client.find_account(args.query)
                if not account:
                    if not args.quiet:
                        print(Terminal.error(f"Account not found: {args.query}"), file=sys.stderr)
                    return 1
                
                try:
                    attachment_data = self.client.get_attachment(args.query, args.attach)
                    
                    # Check if attachment is binary
                    is_binary = self._is_binary_attachment(attachment_data)
                    
                    # If binary and not quiet, prompt user
                    if is_binary and not args.quiet:
                        # Try to get filename from attachment ID
                        attach_filename = args.attach
                        if attach_filename.startswith('att-'):
                            attach_filename = attach_filename[4:]
                        
                        response = input(f'"{attach_filename}" is a binary file, print it anyway (or save)? [y/n/S] ').lower()
                        
                        if response == 's':
                            # Save to file
                            with open(attach_filename, 'wb') as f:
                                written = f.write(attachment_data)
                            print(f"{Terminal.success(f'Wrote {written} bytes to \"{attach_filename}\"')}", file=sys.stderr)
                            return 0
                        elif response != 'y':
                            # Don't print
                            return 0
                    
                    # Output attachment data
                    sys.stdout.buffer.write(attachment_data)
                    return 0
                except Exception as e:
                    if not args.quiet:
                        print(Terminal.error(f"Failed to get attachment: {e}"), file=sys.stderr)
                    return 1
            
            # Handle different search modes
            if args.basic_regexp:
                accounts = self.client.search_accounts_regex(args.query)
                if len(accounts) > 1:
                    if not args.quiet:
                        print(Terminal.error(f"Multiple accounts match: {', '.join(a.fullname for a in accounts)}"), 
                              file=sys.stderr)
                    return 1
                elif not accounts:
                    if not args.quiet:
                        print(Terminal.error(f"Account not found: {args.query}"), file=sys.stderr)
                    return 1
                account = accounts[0]
            elif args.fixed_strings:
                accounts = self.client.search_accounts_fixed(args.query)
                if len(accounts) > 1:
                    if not args.quiet:
                        print(Terminal.error(f"Multiple accounts match: {', '.join(a.fullname for a in accounts)}"), 
                              file=sys.stderr)
                    return 1
                elif not accounts:
                    if not args.quiet:
                        print(Terminal.error(f"Account not found: {args.query}"), file=sys.stderr)
                    return 1
                account = accounts[0]
            else:
                account = self.client.find_account(args.query)
            
            if not account:
                if not args.quiet:
                    print(Terminal.error(f"Account not found: {args.query}"), file=sys.stderr)
                return 1
            
            # Expand secure notes if needed
            from .notes import notes_expand
            expanded_account = notes_expand(account)
            if expanded_account and args.expand_multi:
                account = expanded_account
            
            # Check for custom format string
            if hasattr(args, 'format') and args.format:
                from .format import format_account
                output = format_account(args.format, account)
            # Output specific field
            elif args.password:
                output = account.password
            elif args.username:
                output = account.username
            elif args.url:
                output = account.url
            elif args.notes:
                output = self._expand_notes(account.notes) if args.expand_multi else account.notes
            elif args.id:
                output = account.id
            elif args.name:
                output = account.name
            elif args.field:
                field = account.get_field(args.field)
                if field:
                    output = field.value
                else:
                    if not args.quiet:
                        print(Terminal.error(f"Field not found: {args.field}"), file=sys.stderr)
                    return 1
            elif args.json:
                output = json.dumps(account.to_dict(), indent=2)
            else:
                # Default: show all info
                # Print title header if title-format is specified
                if hasattr(args, 'title_format') and args.title_format:
                    from .format import format_account
                    title = format_account(args.title_format, account)
                    print(title)
                
                output = self._format_account(account, expand_multi=args.expand_multi)
            
            if args.clip:
                if ClipboardManager.copy_to_clipboard(output, self.clipboard_timeout):
                    if not args.quiet:
                        print("Copied to clipboard")
                else:
                    if not args.quiet:
                        print(Terminal.warning("Warning: Could not copy to clipboard"), file=sys.stderr)
            else:
                print(output)
            
            return 0
        except AccountNotFoundException as e:
            if not args.quiet:
                print(Terminal.error(f"Error: {e}"), file=sys.stderr)
            return 1
        except Exception as e:
            if not args.quiet:
                print(Terminal.error(f"Error: {e}"), file=sys.stderr)
            return 1
    
    def cmd_ls(self, args) -> int:
        """Handle ls command"""
        # Set color mode
        Terminal.set_color_mode(Terminal.parse_color_mode(args.color))
        
        # Handle sync option
        sync_mode = self._should_sync(args.sync)
        
        try:
            accounts = self.client.get_accounts(sync=sync_mode)
            
            # Filter by group if specified
            if args.group:
                accounts = [a for a in accounts if a.group == args.group]
            
            # Check for custom format string
            if hasattr(args, 'format') and args.format:
                from .format import format_account
                for account in accounts:
                    print(format_account(args.format, account))
            elif args.json:
                data = [a.to_dict() for a in accounts]
                print(json.dumps(data, indent=2))
            elif args.long:
                # Long format with optional modified time and username
                for account in accounts:
                    parts = [account.id]
                    
                    if args.m:
                        # Add modified time (if available)
                        modified = getattr(account, 'last_modified', 'N/A')
                        parts.append(str(modified))
                    
                    parts.append(Terminal.bold(account.fullname))
                    
                    if args.u or True:  # Always show username in long format
                        parts.append(account.username)
                    
                    print(' '.join(str(p) for p in parts))
            else:
                # Simple format - just fullname
                for account in accounts:
                    if args.u:
                        print(f"{Terminal.bold(account.fullname)} [{account.username}]")
                    else:
                        print(account.fullname)
            
            return 0
        except Exception as e:
            print(Terminal.error(f"Error: {e}"), file=sys.stderr)
            return 1
    
    def cmd_generate(self, args) -> int:
        """Handle generate command"""
        # Handle sync option
        sync_mode = self._should_sync(getattr(args, 'sync', 'auto'))
        
        # Backwards compatibility: if name is a number and no username/url, treat as length
        account_name = args.name
        length = args.length
        
        if account_name and account_name.isdigit() and not args.username and not args.url:
            # Treat first arg as length for backwards compatibility
            length = int(account_name)
            account_name = None
        
        # Generate password
        password = self.client.generate_password(
            length=length,
            symbols=not args.no_symbols
        )
        
        # If name provided, check if account exists or create new one
        if account_name:
            if not self.client.is_logged_in():
                print("Error: not logged in", file=sys.stderr)
                return 1
            
            try:
                # Try to find existing account
                existing_account = None
                try:
                    existing_account = self.client.find_account(account_name, sync=True)
                except:
                    pass
                
                if existing_account:
                    # Update existing account with new password
                    from .notes import notes_expand, notes_collapse
                    
                    # Expand secure notes if needed
                    notes_expanded = notes_expand(existing_account)
                    if notes_expanded:
                        # Update expanded version
                        notes_expanded.password = password
                        if args.username:
                            notes_expanded.username = args.username
                        if args.url:
                            notes_expanded.url = args.url
                        
                        # Collapse back
                        notes_collapsed = notes_collapse(notes_expanded)
                        self.client.update_account(
                            existing_account.id,
                            password=password,
                            notes=notes_collapsed.note
                        )
                    else:
                        # Regular account update
                        update_args = {'password': password}
                        if args.username:
                            update_args['username'] = args.username
                        if args.url:
                            update_args['url'] = args.url
                        self.client.update_account(existing_account.id, **update_args)
                    
                    print(f"Updated password for account: {account_name}")
                else:
                    # Create new account with generated password
                    account_id = self.client.add_account(
                        name=account_name,
                        username=args.username or '',
                        password=password,
                        url=args.url or '',
                        notes='',
                        group=''
                    )
                    
                    print(f"Generated password for new account: {account_name}")
                    if account_id:
                        print(f"Account ID: {account_id}")
                
                if sync_mode:
                    self.client.sync(force=True)
                
                if args.clip:
                    if ClipboardManager.copy_to_clipboard(password, self.clipboard_timeout):
                        print("Password copied to clipboard")
                    else:
                        print(Terminal.warning("Warning: Could not copy to clipboard"), file=sys.stderr)
                else:
                    print(f"Password: {password}")
                
                return 0
            except Exception as e:
                print(f"Failed to update/create account: {e}", file=sys.stderr)
                return 1
        
        # Just generate and display/copy
        
        if args.clip:
            if ClipboardManager.copy_to_clipboard(password, self.clipboard_timeout):
                print("Password copied to clipboard")
            else:
                print(Terminal.warning("Warning: Could not copy to clipboard"), file=sys.stderr)
                print(password)
        else:
            print(password)
        
        return 0
    
    def cmd_sync(self, args) -> int:
        """Handle sync command"""
        # Set color mode
        Terminal.set_color_mode(Terminal.parse_color_mode(args.color))
        
        try:
            if args.background:
                # Fork to background
                import os
                pid = os.fork()
                if pid == 0:
                    # Child process - do sync
                    try:
                        self.client.sync(force=True)
                        sys.exit(0)
                    except Exception:
                        sys.exit(1)
                else:
                    # Parent process
                    print(f"Sync started in background (PID: {pid})")
                    return 0
            else:
                # Foreground sync
                self.client.sync(force=True)
                print("Vault synced successfully")
                return 0
        except Exception as e:
            print(Terminal.error(f"Sync failed: {e}"), file=sys.stderr)
            return 1
    
    def cmd_add(self, args) -> int:
        """Handle add command"""
        import getpass
        import sys
        
        # Set color mode
        Terminal.set_color_mode(Terminal.parse_color_mode(args.color))
        
        if not self.client.is_logged_in():
            print("Error: not logged in", file=sys.stderr)
            return 1
        
        # Handle sync option
        sync_mode = self._should_sync(getattr(args, 'sync', 'auto'))
        
        # Check if this is an application entry
        is_app = getattr(args, 'app', False)
        
        # Check if this should be interactive mode
        # Interactive if no field options provided (except name and note-type)
        has_field_args = (args.username or args.password or args.url or 
                         args.notes or args.generate)
        
        if not has_field_args and not getattr(args, 'non_interactive', False):
            # Interactive mode - launch editor with template
            from .editor import Editor
            
            account_data = {
                'name': args.name,
                'username': '',
                'password': '',
                'url': '',
                'notes': '',
                'fields': []
            }
            
            # Add note type field if specified
            if args.note_type:
                note_type = get_note_type_by_shortname(args.note_type)
                if not note_type:
                    print(f"Error: Unknown note type '{args.note_type}'", file=sys.stderr)
                    return 1
                account_data['fields'].append({
                    'name': 'NoteType',
                    'value': note_type.value,
                    'type': 'text'
                })
            
            # Launch editor
            edited_data = Editor.edit_account_template(account_data)
            if not edited_data:
                print("Cancelled")
                return 0
            
            try:
                # Convert fields list to dict
                fields_dict = {}
                for field in edited_data.get('fields', []):
                    if field.get('name'):
                        fields_dict[field['name']] = field.get('value', '')
                
                # Create account with edited data
                account_id = self.client.add_account(
                    name=edited_data['name'],
                    username=edited_data['username'],
                    password=edited_data['password'],
                    url=edited_data['url'],
                    notes=edited_data['notes'],
                    group=args.group,
                    fields=fields_dict if fields_dict else None
                )
                
                if sync_mode:
                    self.client.sync(force=True)
                
                print(f"Added account: {edited_data['name']}")
                if account_id:
                    print(f"Account ID: {account_id}")
                return 0
            except Exception as e:
                print(f"Failed to add account: {e}", file=sys.stderr)
                return 1
        
        try:
            # Handle secure note types
            if args.note_type:
                note_type = get_note_type_by_shortname(args.note_type)
                if not note_type:
                    print(f"Error: Unknown note type '{args.note_type}'", file=sys.stderr)
                    print("Available types: creditcard, bank, server, sshkey, etc.", file=sys.stderr)
                    return 1
                
                # For secure notes, collect fields interactively
                from .note_types import get_template
                template = get_template(note_type)
                fields = {}
                
                print(f"Creating {template.name} secure note")
                for field_name in template.fields:
                    if field_name.lower() in ['password', 'passphrase', 'pin']:
                        value = getpass.getpass(f"{field_name}: ")
                    else:
                        value = input(f"{field_name}: ")
                    if value:
                        fields[field_name] = value
                
                account_id = self.client.add_secure_note(
                    name=args.name,
                    note_type=note_type,
                    fields=fields,
                    group=args.group
                )
                
                print(f"Added secure note: {args.name}")
                if account_id:
                    print(f"Account ID: {account_id}")
                return 0
            
            # Regular account
            password = args.password
            if args.generate:
                password = self.client.generate_password(length=args.generate)
                print(f"Generated password: {password}")
            elif not password:
                if hasattr(args, 'non_interactive') and args.non_interactive:
                    # Read from stdin in non-interactive mode
                    password = sys.stdin.readline().rstrip('\n')
                else:
                    password = getpass.getpass("Password: ")
            
            # Add account
            account_id = self.client.add_account(
                name=args.name,
                username=args.username,
                password=password,
                url=args.url,
                notes=args.notes,
                group=args.group,
                is_app=is_app
            )
            
            if sync_mode:
                self.client.sync(force=True)
            
            account_type = "application" if is_app else "account"
            print(f"Added {account_type}: {args.name}")
            if account_id:
                print(f"Account ID: {account_id}")
            return 0
        except Exception as e:
            print(f"Failed to add account: {e}", file=sys.stderr)
            return 1
    
    def cmd_edit(self, args) -> int:
        """Handle edit command"""
        import getpass
        import sys
        
        if not self.client.is_logged_in():
            print("Error: not logged in", file=sys.stderr)
            return 1
        
        # Handle sync option
        sync_mode = self._should_sync(getattr(args, 'sync', 'auto'))
        
        try:
            # Check if this should be interactive mode
            has_field_args = (args.name is not None or args.username is not None or 
                            args.password is not None or args.url is not None or 
                            args.notes is not None or args.group is not None or
                            hasattr(args, 'upload_attachment') and args.upload_attachment)
            
            # Handle attachment upload first if specified
            if hasattr(args, 'upload_attachment') and args.upload_attachment:
                from pathlib import Path
                
                filepath = Path(args.upload_attachment)
                if not filepath.exists():
                    print(f"Error: File not found: {filepath}", file=sys.stderr)
                    return 1
                
                try:
                    with open(filepath, 'rb') as f:
                        file_data = f.read()
                    
                    self.client.upload_attachment(args.query, filepath.name, file_data)
                    
                    if sync_mode:
                        self.client.sync(force=True)
                    
                    print(f"Uploaded attachment: {filepath.name}")
                    return 0
                except Exception as e:
                    print(f"Failed to upload attachment: {e}", file=sys.stderr)
                    return 1
            
            if not has_field_args and not getattr(args, 'non_interactive', False):
                # Interactive mode - launch editor with current account data
                from .editor import Editor
                
                # Get current account
                account = self.client.find_account(args.query)
                if not account:
                    print(f"Error: Account not found: {args.query}", file=sys.stderr)
                    return 1
                
                # Prepare account data for template
                account_data = {
                    'name': account.name,
                    'username': account.username,
                    'password': account.password,
                    'url': account.url,
                    'notes': account.notes,
                    'fields': [{'name': f.name, 'value': f.value, 'type': f.type} 
                              for f in account.fields] if account.fields else []
                }
                
                # Launch editor
                edited_data = Editor.edit_account_template(account_data)
                if not edited_data:
                    print("Cancelled")
                    return 0
                
                # Convert fields list to dict
                fields_dict = {}
                for field in edited_data.get('fields', []):
                    if field.get('name'):
                        fields_dict[field['name']] = field.get('value', '')
                
                # Update account with all edited fields
                self.client.update_account(
                    args.query,
                    name=edited_data['name'],
                    username=edited_data['username'],
                    password=edited_data['password'],
                    url=edited_data['url'],
                    notes=edited_data['notes'],
                    fields=fields_dict if fields_dict else None
                )
                
                if sync_mode:
                    self.client.sync(force=True)
                
                print(f"Updated account: {args.query}")
                return 0
            
            # Non-interactive mode - build update dict with only provided fields
            updates = {}
            if args.name is not None:
                updates['name'] = args.name
            if args.username is not None:
                updates['username'] = args.username
            if args.password is not None:
                if not args.password:  # Empty string means prompt
                    if hasattr(args, 'non_interactive') and args.non_interactive:
                        # Read from stdin in non-interactive mode
                        updates['password'] = sys.stdin.readline().rstrip('\n')
                    else:
                        updates['password'] = getpass.getpass("New password: ")
                else:
                    updates['password'] = args.password
            if args.url is not None:
                updates['url'] = args.url
            if args.notes is not None:
                updates['notes'] = args.notes
            if args.group is not None:
                updates['group'] = args.group
            
            if not updates:
                print("No changes specified", file=sys.stderr)
                return 1
            
            # Update account
            self.client.update_account(args.query, **updates)
            
            if sync_mode:
                self.client.sync(force=True)
            
            print(f"Updated account: {args.query}")
            return 0
        except Exception as e:
            print(f"Failed to update account: {e}", file=sys.stderr)
            return 1
    
    def cmd_rm(self, args) -> int:
        """Handle rm command"""
        if not self.client.is_logged_in():
            print("Error: not logged in", file=sys.stderr)
            return 1
        
        # Handle sync option
        sync_mode = self._should_sync(getattr(args, 'sync', 'auto'))
        
        try:
            # Confirm deletion unless --force
            if not args.force:
                response = input(f"Delete account '{args.query}'? (y/N): ")
                if response.lower() != 'y':
                    print("Cancelled")
                    return 0
            
            # Delete account
            self.client.delete_account(args.query)
            
            if sync_mode:
                self.client.sync(force=True)
            
            print(f"Deleted account: {args.query}")
            return 0
        except Exception as e:
            print(f"Failed to delete account: {e}", file=sys.stderr)
            return 1
    
    def cmd_duplicate(self, args) -> int:
        """Handle duplicate command"""
        if not self.client.is_logged_in():
            print("Error: not logged in", file=sys.stderr)
            return 1
        
        # Handle sync option
        sync_mode = self._should_sync(getattr(args, 'sync', 'auto'))
        
        try:
            new_name = args.name if hasattr(args, 'name') and args.name else None
            account_id = self.client.duplicate_account(args.query, new_name)
            
            if sync_mode:
                self.client.sync(force=True)
            
            name = args.name if args.name else f"Copy of {args.query}"
            print(f"Duplicated account: {name}")
            if account_id:
                print(f"New account ID: {account_id}")
            return 0
        except Exception as e:
            print(f"Failed to duplicate account: {e}", file=sys.stderr)
            return 1
    
    def cmd_mv(self, args) -> int:
        """Handle mv command"""
        if not self.client.is_logged_in():
            print("Error: not logged in", file=sys.stderr)
            return 1
        
        # Handle sync option
        sync_mode = self._should_sync(getattr(args, 'sync', 'auto'))
        
        try:
            self.client.move_account(args.query, args.group)
            
            if sync_mode:
                self.client.sync(force=True)
            
            print(f"Moved account '{args.query}' to group '{args.group}'")
            return 0
        except Exception as e:
            print(f"Failed to move account: {e}", file=sys.stderr)
            return 1
    
    def _format_account(self, account: Account, expand_multi: bool = False) -> str:
        """Format account for display"""
        lines = [
            f"{Terminal.header('Name')}: {account.name}",
            f"{Terminal.header('Fullname')}: {account.fullname}",
            f"{Terminal.header('Username')}: {account.username}",
            f"{Terminal.header('Password')}: {account.password}",
            f"{Terminal.header('URL')}: {account.url}",
        ]
        
        if account.notes:
            notes = self._expand_notes(account.notes) if expand_multi else account.notes
            lines.append(f"{Terminal.header('Notes')}: {notes}")
        
        if account.fields:
            lines.append(f"{Terminal.header('Fields')}:")
            for field in account.fields:
                lines.append(f"  {field.name}: {field.value}")
        
        return "\n".join(lines)
    
    def _expand_notes(self, notes: str) -> str:
        """Expand multi-line fields in notes (fix ASCII armor newlines)"""
        # Fix PGP ASCII armor where newlines were replaced with spaces
        if not notes:
            return notes
        
        # Look for PGP armor patterns
        armor_pattern = r'-----BEGIN ([A-Z ]+)-----(.+?)-----END \1-----'
        
        def fix_armor(match):
            header = match.group(1)
            content = match.group(2)
            
            # Replace spaces with newlines in the content, but not after colons (headers)
            lines = []
            current = []
            for char in content:
                if char == ' ':
                    if current and current[-1] != ':':
                        lines.append(''.join(current))
                        current = []
                    else:
                        current.append(char)
                else:
                    current.append(char)
            if current:
                lines.append(''.join(current))
            
            fixed_content = '\n'.join(lines)
            return f"-----BEGIN {header}-----\n{fixed_content}\n-----END {header}-----"
        
        return re.sub(armor_pattern, fix_armor, notes, flags=re.DOTALL)
    
    def cmd_export(self, args) -> int:
        """Handle export command"""
        if not self.client.is_logged_in():
            print("Error: not logged in", file=sys.stderr)
            return 1
        
        # Handle sync option - always sync before export
        sync_mode = self._should_sync(getattr(args, 'sync', 'auto'))
        if sync_mode:
            try:
                self.client.sync(force=True)
            except Exception:
                pass  # Continue with cached data if sync fails
        
        try:
            fields = parse_csv_field_list(args.fields) if args.fields else None
            
            if args.output:
                with open(args.output, 'w') as f:
                    self.client.export_to_csv(fields, f)
                print(f"Exported to {args.output}")
            else:
                csv_data = self.client.export_to_csv(fields)
                print(csv_data)
            
            return 0
        except Exception as e:
            print(f"Export failed: {e}", file=sys.stderr)
            return 1
    
    def cmd_import(self, args) -> int:
        """Handle import command"""
        if not self.client.is_logged_in():
            print("Error: not logged in", file=sys.stderr)
            return 1
        
        # Handle sync option
        sync_mode = self._should_sync(getattr(args, 'sync', 'auto'))
        
        try:
            # Read CSV data
            if args.file:
                with open(args.file, 'r') as f:
                    csv_data = f.read()
            else:
                # Read from stdin
                csv_data = sys.stdin.read()
            
            count = self.client.import_from_csv(csv_data, args.keep_dupes)
            
            if sync_mode:
                self.client.sync(force=True)
            
            print(f"Imported {count} accounts")
            return 0
        except Exception as e:
            print(f"Import failed: {e}", file=sys.stderr)
            return 1
    
    def cmd_passwd(self, args) -> int:
        """Handle passwd command"""
        if not self.client.is_logged_in():
            print("Error: not logged in", file=sys.stderr)
            return 1
        
        try:
            current_password = getpass.getpass("Current Master Password: ")
            new_password = getpass.getpass("New Master Password: ")
            confirm_password = getpass.getpass("Confirm New Master Password: ")
            
            if new_password != confirm_password:
                print("Error: Passwords do not match", file=sys.stderr)
                return 1
            
            self.client.change_password(current_password, new_password)
            print("Password changed successfully")
            return 0
        except NotImplementedError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"Failed to change password: {e}", file=sys.stderr)
            return 1
    
    def cmd_share_create(self, args) -> int:
        """Handle share create command"""
        if not self.client.is_logged_in():
            print("Error: not logged in", file=sys.stderr)
            return 1
        
        try:
            share_id = self.client.create_share(args.name)
            print(f"Created shared folder: {args.name}")
            if share_id:
                print(f"Share ID: {share_id}")
            return 0
        except Exception as e:
            print(f"Failed to create share: {e}", file=sys.stderr)
            return 1
    
    def cmd_share_rm(self, args) -> int:
        """Handle share rm command"""
        if not self.client.is_logged_in():
            print("Error: not logged in", file=sys.stderr)
            return 1
        
        try:
            self.client.delete_share(args.name)
            print(f"Deleted shared folder: {args.name}")
            return 0
        except Exception as e:
            print(f"Failed to delete share: {e}", file=sys.stderr)
            return 1
    
    def cmd_share_userls(self, args) -> int:
        """Handle share userls command"""
        if not self.client.is_logged_in():
            print("Error: not logged in", file=sys.stderr)
            return 1
        
        try:
            users = self.client.list_share_users(args.name)
            
            if not users:
                print("No users found")
                return 0
            
            # Print user table
            print(f"{'Username':<30} {'Real Name':<25} {'RO':<3} {'Admin':<5} {'Hidden':<6} {'Status':<10}")
            print("-" * 90)
            
            for user in users:
                ro = "x" if user.get('readonly', False) else "_"
                admin = "x" if user.get('admin', False) else "_"
                hidden = "x" if user.get('hide_passwords', False) else "_"
                status = "Accepted" if user.get('accepted', False) else "Pending"
                
                print(f"{user.get('username', ''):<30} {user.get('realname', ''):<25} "
                      f"{ro:<3} {admin:<5} {hidden:<6} {status:<10}")
            
            return 0
        except Exception as e:
            print(f"Failed to list share users: {e}", file=sys.stderr)
            return 1
    
    def cmd_share_useradd(self, args) -> int:
        """Handle share useradd command"""
        if not self.client.is_logged_in():
            print("Error: not logged in", file=sys.stderr)
            return 1
        
        try:
            self.client.add_share_user(
                args.name,
                args.username,
                readonly=args.read_only,
                admin=args.admin,
                hide_passwords=args.hidden
            )
            print(f"Added user {args.username} to {args.name}")
            return 0
        except Exception as e:
            print(f"Failed to add user to share: {e}", file=sys.stderr)
            return 1
    
    def cmd_share_userdel(self, args) -> int:
        """Handle share userdel command"""
        if not self.client.is_logged_in():
            print("Error: not logged in", file=sys.stderr)
            return 1
        
        try:
            self.client.remove_share_user(args.name, args.username)
            print(f"Removed user {args.username} from {args.name}")
            return 0
        except Exception as e:
            print(f"Failed to remove user from share: {e}", file=sys.stderr)
            return 1
    
    def cmd_share_usermod(self, args) -> int:
        """Handle share usermod command"""
        if not self.client.is_logged_in():
            print("Error: not logged in", file=sys.stderr)
            return 1
        
        try:
            self.client.update_share_user(
                args.name,
                args.username,
                readonly=args.read_only,
                admin=args.admin,
                hide_passwords=args.hidden
            )
            print(f"Updated permissions for {args.username} in {args.name}")
            return 0
        except Exception as e:
            print(f"Failed to update user permissions: {e}", file=sys.stderr)
            return 1
    
    def cmd_share_limit(self, args) -> int:
        """Handle share limit command"""
        if not self.client.is_logged_in():
            print("Error: not logged in", file=sys.stderr)
            return 1
        
        try:
            # Show current limits
            if args.show:
                limits = self.client.get_share_limits(args.name, args.username)
                
                if limits is None:
                    print("No limits set")
                    return 0
                
                limit_type = "Deny list" if limits.whitelist is False else "Allow list"
                print(f"Limit type: {limit_type}")
                
                if limits.account_ids:
                    print(f"Accounts ({len(limits.account_ids)}):")
                    for account_id in limits.account_ids:
                        print(f"  - {account_id}")
                else:
                    print("No accounts in limit list")
                
                return 0
            
            # Clear all limits
            if args.clear:
                from .models import ShareLimit
                empty_limit = ShareLimit(whitelist=True, account_ids=[])
                self.client.set_share_limits(args.name, args.username, empty_limit)
                print(f"Cleared all limits for {args.username} in {args.name}")
                return 0
            
            # Get current limits to modify
            current_limits = self.client.get_share_limits(args.name, args.username)
            
            # Determine whitelist mode
            if args.deny:
                whitelist = False
            elif args.allow:
                whitelist = True
            else:
                # Use current setting or default to allow
                whitelist = current_limits.whitelist if current_limits else True
            
            # Get current account IDs list
            current_ids = set(current_limits.account_ids) if current_limits else set()
            
            # Modify account IDs list
            if args.add:
                current_ids.update(args.sites)
                print(f"Added {len(args.sites)} account(s) to limit")
            elif args.rm:
                current_ids.difference_update(args.sites)
                print(f"Removed {len(args.sites)} account(s) from limit")
            else:
                # Replace entire list
                current_ids = set(args.sites)
                print(f"Set limit to {len(args.sites)} account(s)")
            
            # Create and set new limit
            from .models import ShareLimit
            new_limit = ShareLimit(whitelist=whitelist, account_ids=list(current_ids))
            self.client.set_share_limits(args.name, args.username, new_limit)
            
            limit_type = "deny" if not whitelist else "allow"
            print(f"Updated {limit_type} list for {args.username} in {args.name}")
            return 0
            
        except Exception as e:
            print(f"Failed to manage share limits: {e}", file=sys.stderr)
            return 1


def main():
    """Main entry point"""
    # Set process name for security
    try:
        from .process_security import ProcessSecurity
        ProcessSecurity.set_process_name('lpass')
    except Exception:
        # Silently ignore if process name setting fails
        pass
    
    cli = CLI()
    sys.exit(cli.run())


if __name__ == '__main__':
    main()

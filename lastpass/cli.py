"""
Command-line interface for LastPass
"""

import sys
import argparse
import json
import getpass
from typing import Optional, List
from pathlib import Path

from . import __version__
from .client import LastPassClient
from .exceptions import LastPassException, AccountNotFoundException
from .models import Account


class CLI:
    """Command-line interface handler"""
    
    def __init__(self):
        self.client = LastPassClient()
    
    def run(self, args: Optional[List[str]] = None) -> int:
        """Run CLI with arguments"""
        parser = self._create_parser()
        
        if args is None:
            args = sys.argv[1:]
        
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
        login_parser.set_defaults(func=self.cmd_login)
        
        # Logout
        logout_parser = subparsers.add_parser('logout', help='Logout from LastPass')
        logout_parser.add_argument('--force', '-f', action='store_true',
                                 help='Force logout')
        logout_parser.set_defaults(func=self.cmd_logout)
        
        # Status
        status_parser = subparsers.add_parser('status', help='Show login status')
        status_parser.add_argument('--quiet', '-q', action='store_true',
                                 help='Quiet mode')
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
        show_parser.add_argument('--field', metavar='FIELD',
                               help='Show only specified field')
        show_parser.add_argument('--json', '-j', action='store_true',
                               help='Output as JSON')
        show_parser.add_argument('--clip', '-c', action='store_true',
                               help='Copy to clipboard')
        show_parser.set_defaults(func=self.cmd_show)
        
        # List
        ls_parser = subparsers.add_parser('ls', help='List accounts')
        ls_parser.add_argument('group', nargs='?', help='Filter by group')
        ls_parser.add_argument('--long', '-l', action='store_true',
                             help='Long listing format')
        ls_parser.add_argument('--json', '-j', action='store_true',
                             help='Output as JSON')
        ls_parser.set_defaults(func=self.cmd_ls)
        
        # Generate
        generate_parser = subparsers.add_parser('generate', 
                                               help='Generate password')
        generate_parser.add_argument('length', type=int, nargs='?', default=16,
                                   help='Password length (default: 16)')
        generate_parser.add_argument('--no-symbols', action='store_true',
                                   help='Exclude symbols')
        generate_parser.add_argument('--clip', '-c', action='store_true',
                                   help='Copy to clipboard')
        generate_parser.set_defaults(func=self.cmd_generate)
        
        # Sync
        sync_parser = subparsers.add_parser('sync', help='Sync vault from server')
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
        edit_parser.set_defaults(func=self.cmd_edit)
        
        # Remove
        rm_parser = subparsers.add_parser('rm', help='Remove account')
        rm_parser.add_argument('query', help='Account name, ID, or URL')
        rm_parser.add_argument('--force', '-f', action='store_true',
                             help='Skip confirmation')
        rm_parser.set_defaults(func=self.cmd_rm)
        
        # Duplicate
        duplicate_parser = subparsers.add_parser('duplicate', help='Duplicate account')
        duplicate_parser.add_argument('query', help='Account name, ID, or URL')
        duplicate_parser.add_argument('--name', help='Name for duplicate')
        duplicate_parser.set_defaults(func=self.cmd_duplicate)
        
        # Move
        mv_parser = subparsers.add_parser('mv', help='Move account to different group')
        mv_parser.add_argument('query', help='Account name, ID, or URL')
        mv_parser.add_argument('group', help='New group/folder name')
        mv_parser.set_defaults(func=self.cmd_mv)
        
        return parser
    
    def cmd_login(self, args) -> int:
        """Handle login command"""
        password = getpass.getpass("Master Password: ")
        
        try:
            self.client.login(
                args.username,
                password,
                trust=args.trust,
                otp=args.otp,
                force=args.force
            )
            print(f"Success: Logged in as {args.username}")
            return 0
        except Exception as e:
            print(f"Login failed: {e}", file=sys.stderr)
            return 1
    
    def cmd_logout(self, args) -> int:
        """Handle logout command"""
        try:
            self.client.logout(force=args.force)
            print("Logged out successfully")
            return 0
        except Exception as e:
            print(f"Logout failed: {e}", file=sys.stderr)
            return 1
    
    def cmd_status(self, args) -> int:
        """Handle status command"""
        if self.client.is_logged_in():
            if not args.quiet:
                print(f"Logged in as {self.client.session.uid}")
            return 0
        else:
            if not args.quiet:
                print("Not logged in")
            return 1
    
    def cmd_show(self, args) -> int:
        """Handle show command"""
        try:
            account = self.client.find_account(args.query)
            
            if not account:
                print(f"Account not found: {args.query}", file=sys.stderr)
                return 1
            
            # Output specific field
            if args.password:
                output = account.password
            elif args.username:
                output = account.username
            elif args.url:
                output = account.url
            elif args.notes:
                output = account.notes
            elif args.field:
                field = account.get_field(args.field)
                if field:
                    output = field.value
                else:
                    print(f"Field not found: {args.field}", file=sys.stderr)
                    return 1
            elif args.json:
                output = json.dumps(account.to_dict(), indent=2)
            else:
                # Default: show all info
                output = self._format_account(account)
            
            if args.clip:
                self._copy_to_clipboard(output)
                print("Copied to clipboard")
            else:
                print(output)
            
            return 0
        except AccountNotFoundException as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
    
    def cmd_ls(self, args) -> int:
        """Handle ls command"""
        try:
            accounts = self.client.get_accounts()
            
            # Filter by group if specified
            if args.group:
                accounts = [a for a in accounts if a.group == args.group]
            
            if args.json:
                data = [a.to_dict() for a in accounts]
                print(json.dumps(data, indent=2))
            elif args.long:
                for account in accounts:
                    print(f"{account.id:10} {account.fullname:40} {account.username:30}")
            else:
                for account in accounts:
                    print(account.fullname)
            
            return 0
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
    
    def cmd_generate(self, args) -> int:
        """Handle generate command"""
        password = self.client.generate_password(
            length=args.length,
            symbols=not args.no_symbols
        )
        
        if args.clip:
            self._copy_to_clipboard(password)
            print("Password copied to clipboard")
        else:
            print(password)
        
        return 0
    
    def cmd_sync(self, args) -> int:
        """Handle sync command"""
        try:
            self.client.sync(force=True)
            print("Vault synced successfully")
            return 0
        except Exception as e:
            print(f"Sync failed: {e}", file=sys.stderr)
            return 1
    
    def cmd_add(self, args) -> int:
        """Handle add command"""
        import getpass
        
        if not self.client.is_logged_in():
            print("Error: not logged in", file=sys.stderr)
            return 1
        
        try:
            # Handle password
            password = args.password
            if args.generate:
                password = self.client.generate_password(length=args.generate)
                print(f"Generated password: {password}")
            elif not password:
                password = getpass.getpass("Password: ")
            
            # Add account
            account_id = self.client.add_account(
                name=args.name,
                username=args.username,
                password=password,
                url=args.url,
                notes=args.notes,
                group=args.group
            )
            
            print(f"Added account: {args.name}")
            if account_id:
                print(f"Account ID: {account_id}")
            return 0
        except Exception as e:
            print(f"Failed to add account: {e}", file=sys.stderr)
            return 1
    
    def cmd_edit(self, args) -> int:
        """Handle edit command"""
        import getpass
        
        if not self.client.is_logged_in():
            print("Error: not logged in", file=sys.stderr)
            return 1
        
        try:
            # Build update dict with only provided fields
            updates = {}
            if args.name is not None:
                updates['name'] = args.name
            if args.username is not None:
                updates['username'] = args.username
            if args.password is not None:
                if not args.password:  # Empty string means prompt
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
        
        try:
            # Confirm deletion unless --force
            if not args.force:
                response = input(f"Delete account '{args.query}'? (y/N): ")
                if response.lower() != 'y':
                    print("Cancelled")
                    return 0
            
            # Delete account
            self.client.delete_account(args.query)
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
        
        try:
            new_name = args.name if hasattr(args, 'name') and args.name else None
            account_id = self.client.duplicate_account(args.query, new_name)
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
        
        try:
            self.client.move_account(args.query, args.group)
            print(f"Moved account '{args.query}' to group '{args.group}'")
            return 0
        except Exception as e:
            print(f"Failed to move account: {e}", file=sys.stderr)
            return 1
    
    def _format_account(self, account: Account) -> str:
        """Format account for display"""
        lines = [
            f"Name: {account.name}",
            f"Fullname: {account.fullname}",
            f"Username: {account.username}",
            f"Password: {account.password}",
            f"URL: {account.url}",
        ]
        
        if account.notes:
            lines.append(f"Notes: {account.notes}")
        
        if account.fields:
            lines.append("Fields:")
            for field in account.fields:
                lines.append(f"  {field.name}: {field.value}")
        
        return "\n".join(lines)
    
    def _copy_to_clipboard(self, text: str) -> None:
        """Copy text to clipboard"""
        try:
            import pyperclip
            pyperclip.copy(text)
        except ImportError:
            # Try using system commands
            import subprocess
            import platform
            
            system = platform.system()
            
            try:
                if system == "Darwin":  # macOS
                    subprocess.run(['pbcopy'], input=text.encode(), check=True)
                elif system == "Linux":
                    # Try xclip first, then xsel
                    try:
                        subprocess.run(['xclip', '-selection', 'clipboard'],
                                     input=text.encode(), check=True)
                    except FileNotFoundError:
                        subprocess.run(['xsel', '--clipboard', '--input'],
                                     input=text.encode(), check=True)
                else:
                    print("Clipboard not supported on this platform", 
                          file=sys.stderr)
            except (FileNotFoundError, subprocess.CalledProcessError):
                print("Could not copy to clipboard. Install xclip, xsel, or pyperclip",
                      file=sys.stderr)


def main():
    """Main entry point"""
    cli = CLI()
    sys.exit(cli.run())


if __name__ == '__main__':
    main()

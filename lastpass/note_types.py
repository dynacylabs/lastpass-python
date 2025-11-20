"""
Secure note types and templates for LastPass
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


class NoteType(Enum):
    """Supported secure note types"""
    NONE = -1
    GENERIC = 0
    AMEX = 1
    BANK = 2
    CREDIT = 3
    DATABASE = 4
    DRIVERS_LICENSE = 5
    EMAIL = 6
    HEALTH_INSURANCE = 7
    IM = 8
    INSURANCE = 9
    MASTERCARD = 10
    MEMBERSHIP = 11
    PASSPORT = 12
    SERVER = 13
    SOFTWARE_LICENSE = 14
    SSH_KEY = 15
    SSN = 16
    VISA = 17
    WIFI = 18


@dataclass
class NoteTemplate:
    """Template definition for a note type"""
    shortname: str
    name: str
    fields: List[str]
    multiline_fields: List[str] = None
    
    def __post_init__(self):
        if self.multiline_fields is None:
            self.multiline_fields = []


# Note type templates matching lastpass-cli
NOTE_TEMPLATES = {
    NoteType.GENERIC: NoteTemplate(
        shortname="generic",
        name="Generic",
        fields=[],
    ),
    NoteType.AMEX: NoteTemplate(
        shortname="amex",
        name="American Express",
        fields=[
            "Name on Card",
            "Type",
            "Number",
            "Security Code",
            "Start Date",
            "Expiration Date",
            "Name",
            "Address",
            "City / Town",
            "State",
            "ZIP / Postal Code",
            "Country",
            "Telephone",
        ],
    ),
    NoteType.BANK: NoteTemplate(
        shortname="bank",
        name="Bank Account",
        fields=[
            "Bank Name",
            "Account Type",
            "Routing Number",
            "Account Number",
            "SWIFT Code",
            "IBAN Number",
            "Pin",
            "Branch Address",
            "Branch Phone",
        ],
    ),
    NoteType.CREDIT: NoteTemplate(
        shortname="creditcard",
        name="Credit Card",
        fields=[
            "Name on Card",
            "Type",
            "Number",
            "Security Code",
            "Start Date",
            "Expiration Date",
            "Name",
            "Address",
            "City / Town",
            "State",
            "ZIP / Postal Code",
            "Country",
            "Telephone",
        ],
    ),
    NoteType.DATABASE: NoteTemplate(
        shortname="database",
        name="Database",
        fields=[
            "Type",
            "Hostname",
            "Port",
            "Database",
            "Username",
            "Password",
            "SID",
            "Alias",
        ],
    ),
    NoteType.DRIVERS_LICENSE: NoteTemplate(
        shortname="driverslicense",
        name="Driver's License",
        fields=[
            "Number",
            "Expiration Date",
            "License Class",
            "Name",
            "Address",
            "City / Town",
            "State",
            "ZIP / Postal Code",
            "Country",
            "Date of Birth",
            "Sex",
            "Height",
        ],
    ),
    NoteType.EMAIL: NoteTemplate(
        shortname="email",
        name="Email Account",
        fields=[
            "Username",
            "Password",
            "Server",
            "Port",
            "Type",
            "SMTP Server",
            "SMTP Port",
        ],
    ),
    NoteType.HEALTH_INSURANCE: NoteTemplate(
        shortname="health-insurance",
        name="Health Insurance",
        fields=[
            "Company",
            "Company Phone",
            "Policy Type",
            "Policy Number",
            "Group ID",
            "Member Name",
            "Member ID",
            "Physician Name",
            "Physician Phone",
            "Physician Address",
            "Co-pay",
        ],
    ),
    NoteType.IM: NoteTemplate(
        shortname="im",
        name="Instant Messenger",
        fields=[
            "Type",
            "Username",
            "Password",
            "Server",
            "Port",
        ],
    ),
    NoteType.INSURANCE: NoteTemplate(
        shortname="insurance",
        name="Insurance",
        fields=[
            "Company",
            "Policy Type",
            "Policy Number",
            "Expiration",
            "Agent Name",
            "Agent Phone",
            "URL",
            "Username",
            "Password",
        ],
    ),
    NoteType.MASTERCARD: NoteTemplate(
        shortname="mastercard",
        name="Mastercard",
        fields=[
            "Name on Card",
            "Type",
            "Number",
            "Security Code",
            "Start Date",
            "Expiration Date",
            "Name",
            "Address",
            "City / Town",
            "State",
            "ZIP / Postal Code",
            "Country",
            "Telephone",
        ],
    ),
    NoteType.MEMBERSHIP: NoteTemplate(
        shortname="membership",
        name="Membership",
        fields=[
            "Organization",
            "Membership Number",
            "Member Name",
            "Start Date",
            "Expiration Date",
            "Website",
            "Telephone",
            "Password",
        ],
    ),
    NoteType.PASSPORT: NoteTemplate(
        shortname="passport",
        name="Passport",
        fields=[
            "Type",
            "Name",
            "Country",
            "Number",
            "Sex",
            "Nationality",
            "Issuing Authority",
            "Date of Birth",
            "Issued Date",
            "Expiration Date",
        ],
    ),
    NoteType.SERVER: NoteTemplate(
        shortname="server",
        name="Server",
        fields=[
            "Hostname",
            "Username",
            "Password",
        ],
    ),
    NoteType.SOFTWARE_LICENSE: NoteTemplate(
        shortname="software-license",
        name="Software License",
        fields=[
            "License Key",
            "Licensee",
            "Version",
            "Publisher",
            "Support Email",
            "Website",
            "Price",
            "Purchase Date",
            "Order Number",
            "Number of Licenses",
            "Order Total",
        ],
    ),
    NoteType.SSH_KEY: NoteTemplate(
        shortname="sshkey",
        name="SSH Key",
        fields=[
            "Bit Strength",
            "Format",
            "Passphrase",
            "Private Key",
            "Public Key",
            "Hostname",
            "Date",
        ],
        multiline_fields=["Private Key", "Public Key"],
    ),
    NoteType.SSN: NoteTemplate(
        shortname="ssn",
        name="Social Security",
        fields=[
            "Name",
            "Number",
        ],
    ),
    NoteType.VISA: NoteTemplate(
        shortname="visa",
        name="VISA",
        fields=[
            "Name on Card",
            "Type",
            "Number",
            "Security Code",
            "Start Date",
            "Expiration Date",
            "Name",
            "Address",
            "City / Town",
            "State",
            "ZIP / Postal Code",
            "Country",
            "Telephone",
        ],
    ),
    NoteType.WIFI: NoteTemplate(
        shortname="wifi",
        name="WiFi Password",
        fields=[
            "SSID",
            "Password",
            "Connection Type",
            "Connection Mode",
            "Authentication",
            "Encryption",
            "Use 802.1X",
            "FIPS Mode",
            "Key Type",
            "Protected",
            "Key Index",
        ],
    ),
}


def get_note_type_by_shortname(shortname: str) -> Optional[NoteType]:
    """Get note type by shortname"""
    shortname_lower = shortname.lower()
    for note_type, template in NOTE_TEMPLATES.items():
        if template.shortname == shortname_lower:
            return note_type
    return None


def get_note_type_by_name(name: str) -> Optional[NoteType]:
    """Get note type by full name"""
    name_lower = name.lower()
    for note_type, template in NOTE_TEMPLATES.items():
        if template.name.lower() == name_lower:
            return note_type
    return None


def get_template(note_type: NoteType) -> Optional[NoteTemplate]:
    """Get template for a note type"""
    return NOTE_TEMPLATES.get(note_type)


def is_multiline_field(note_type: NoteType, field_name: str) -> bool:
    """Check if a field should be multiline"""
    template = get_template(note_type)
    if template and template.multiline_fields:
        return field_name in template.multiline_fields
    return False


def has_field(note_type: NoteType, field_name: str) -> bool:
    """Check if note type has a specific field"""
    template = get_template(note_type)
    if template:
        return field_name in template.fields
    return False


def format_note_fields(note_type: NoteType, fields: Dict[str, str]) -> str:
    """Format fields into LastPass note format"""
    template = get_template(note_type)
    if not template or note_type == NoteType.GENERIC:
        # Generic note - just return fields as key:value
        lines = []
        for key, value in fields.items():
            lines.append(f"{key}:{value}")
        return "\n".join(lines)
    
    # Structured note with template
    lines = [f"NoteType:{template.name}"]
    for field_name in template.fields:
        value = fields.get(field_name, "")
        lines.append(f"{field_name}:{value}")
    
    # Add any extra fields not in template
    for key, value in fields.items():
        if key not in template.fields:
            lines.append(f"{key}:{value}")
    
    return "\n".join(lines)


def parse_note_fields(notes: str) -> tuple[Optional[NoteType], Dict[str, str]]:
    """Parse note fields from LastPass note format"""
    lines = notes.split("\n")
    fields = {}
    note_type = NoteType.GENERIC
    
    for line in lines:
        if ":" not in line:
            continue
        
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        
        if key == "NoteType":
            note_type = get_note_type_by_name(value) or NoteType.GENERIC
        else:
            fields[key] = value
    
    return note_type, fields

"""
Data models for LastPass entities
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class Field:
    """Custom field in an account"""
    name: str
    value: str
    type: str = "text"
    checked: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "type": self.type,
            "checked": self.checked,
        }


@dataclass
class Attachment:
    """File attachment for an account"""
    id: str
    parent_id: str
    mimetype: str
    filename: str
    size: str
    storage_key: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "parent_id": self.parent_id,
            "mimetype": self.mimetype,
            "filename": self.filename,
            "size": self.size,
        }


@dataclass
class Share:
    """Shared folder information"""
    id: str
    name: str
    key: bytes
    readonly: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "readonly": self.readonly,
        }


@dataclass
class ShareUser:
    """User in a shared folder"""
    username: str
    uid: str = ""
    realname: str = ""
    readonly: bool = False
    admin: bool = False
    hide_passwords: bool = False
    accepted: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "username": self.username,
            "uid": self.uid,
            "realname": self.realname,
            "readonly": self.readonly,
            "admin": self.admin,
            "hide_passwords": self.hide_passwords,
            "accepted": self.accepted,
        }


@dataclass
class ShareLimit:
    """Share limit configuration (whitelist/blacklist of accounts)"""
    whitelist: bool = False  # If True, account_ids is whitelist; if False, blacklist
    account_ids: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "whitelist": self.whitelist,
            "account_ids": self.account_ids,
        }


@dataclass
class Account:
    """LastPass account/entry in the vault"""
    id: str
    name: str
    username: str = ""
    password: str = ""
    url: str = ""
    group: str = ""
    notes: str = ""
    fullname: str = ""
    last_touch: str = ""
    last_modified_gmt: str = ""
    pwprotect: bool = False
    favorite: bool = False
    is_app: bool = False
    attach_present: bool = False
    attachkey: str = ""
    fields: List[Field] = field(default_factory=list)
    attachments: List[Attachment] = field(default_factory=list)
    share: Optional[Share] = None
    
    # App-specific fields (when is_app=True)
    appname: str = ""
    wintitle: str = ""
    wininfo: str = ""
    exeversion: str = ""
    warnversion: str = ""
    exehash: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert account to dictionary"""
        data = {
            "id": self.id,
            "name": self.name,
            "username": self.username,
            "password": self.password,
            "url": self.url,
            "group": self.group,
            "notes": self.notes,
            "fullname": self.fullname,
            "last_touch": self.last_touch,
            "last_modified_gmt": self.last_modified_gmt,
            "pwprotect": self.pwprotect,
            "favorite": self.favorite,
            "is_app": self.is_app,
            "attach_present": self.attach_present,
        }
        
        if self.is_app:
            data["appname"] = self.appname
            data["wintitle"] = self.wintitle
            data["wininfo"] = self.wininfo
            data["exeversion"] = self.exeversion
            data["warnversion"] = self.warnversion
            data["exehash"] = self.exehash
        
        if self.fields:
            data["fields"] = [f.to_dict() for f in self.fields]
        
        if self.attachments:
            data["attachments"] = [a.to_dict() for a in self.attachments]
        
        if self.share:
            data["share"] = self.share.to_dict()
        
        return data
    
    def get_field(self, name: str) -> Optional[Field]:
        """Get a custom field by name"""
        for f in self.fields:
            if f.name == name:
                return f
        return None
    
    def is_secure_note(self) -> bool:
        """Check if this is a secure note"""
        return self.url == "http://sn"

"""
Email connector - IMAP polling for newsletters
"""
import email
import hashlib
import re
from email.header import decode_header
from typing import List, Dict, Any, Optional
from datetime import datetime
import imaplib

from bs4 import BeautifulSoup
import html2text

from app.core.config import settings
from app.db.models.source import SourceConfig
from .base import BaseConnector


class EmailConnector(BaseConnector):
    """Connector for email newsletters via IMAP"""
    
    def __init__(self, config: SourceConfig):
        super().__init__(config)
        self.h2t = html2text.HTML2Text()
        self.h2t.ignore_links = False
        self.h2t.ignore_images = True
        self.h2t.body_width = 0
    
    def _connect(self) -> imaplib.IMAP4_SSL:
        """Connect to IMAP server"""
        if settings.imap_use_ssl:
            mail = imaplib.IMAP4_SSL(settings.imap_host, settings.imap_port)
        else:
            mail = imaplib.IMAP4(settings.imap_host, settings.imap_port)
        
        mail.login(settings.imap_user, settings.imap_password)
        return mail
    
    def _decode_header_value(self, value: str) -> str:
        """Decode email header value"""
        if not value:
            return ""
        
        decoded_parts = []
        for part, encoding in decode_header(value):
            if isinstance(part, bytes):
                try:
                    decoded_parts.append(part.decode(encoding or 'utf-8', errors='replace'))
                except:
                    decoded_parts.append(part.decode('utf-8', errors='replace'))
            else:
                decoded_parts.append(part)
        
        return ' '.join(decoded_parts)
    
    def _get_message_id(self, msg: email.message.Message) -> str:
        """Get a unique ID for the message"""
        message_id = msg.get('Message-ID', '')
        if message_id:
            return hashlib.sha256(message_id.encode()).hexdigest()[:32]
        
        # Fallback: hash of from + date + subject
        from_addr = msg.get('From', '')
        date = msg.get('Date', '')
        subject = msg.get('Subject', '')
        fallback = f"{from_addr}{date}{subject}"
        return hashlib.sha256(fallback.encode()).hexdigest()[:32]
    
    def _extract_text(self, msg: email.message.Message) -> tuple[str, str]:
        """Extract text and HTML content from email"""
        text_content = ""
        html_content = ""
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == 'text/plain':
                    try:
                        text_content = part.get_payload(decode=True).decode('utf-8', errors='replace')
                    except:
                        pass
                elif content_type == 'text/html':
                    try:
                        html_content = part.get_payload(decode=True).decode('utf-8', errors='replace')
                    except:
                        pass
        else:
            content_type = msg.get_content_type()
            try:
                payload = msg.get_payload(decode=True).decode('utf-8', errors='replace')
                if content_type == 'text/html':
                    html_content = payload
                else:
                    text_content = payload
            except:
                pass
        
        return text_content, html_content
    
    def _html_to_text(self, html: str) -> str:
        """Convert HTML to clean text"""
        if not html:
            return ""
        
        # Use html2text for conversion
        text = self.h2t.handle(html)
        
        # Clean up extra whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' +', ' ', text)
        
        return text.strip()
    
    def _extract_links(self, html: str) -> List[str]:
        """Extract all links from HTML"""
        if not html:
            return []
        
        soup = BeautifulSoup(html, 'lxml')
        links = []
        
        for a in soup.find_all('a', href=True):
            href = a['href']
            # Filter out mailto, javascript, and anchors
            if href.startswith(('http://', 'https://')) and 'unsubscribe' not in href.lower():
                links.append(href)
        
        return list(set(links))
    
    def _find_primary_link(self, links: List[str], text: str) -> Optional[str]:
        """Find the most likely primary/action link"""
        # Priority keywords
        priority_keywords = [
            'candidat', 'postuler', 'repondre', 'reply', 'particip',
            'inscription', 'register', 'apply', 'submit', 'formulaire',
            'appel', 'consultation', 'marche', 'tender'
        ]
        
        for link in links:
            link_lower = link.lower()
            for keyword in priority_keywords:
                if keyword in link_lower:
                    return link
        
        # Return first non-image link
        for link in links:
            if not any(ext in link.lower() for ext in ['.jpg', '.png', '.gif', '.svg']):
                return link
        
        return links[0] if links else None
    
    async def fetch(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Fetch emails from IMAP folder"""
        items = []
        mail = None
        
        try:
            mail = self._connect()
            folder = self.config.email_folder or settings.imap_folder
            
            status, _ = mail.select(folder)
            if status != 'OK':
                self.log_error(f"Could not select folder: {folder}")
                return items
            
            # Search for unread emails or all recent
            search_criteria = 'UNSEEN'
            if self.config.email_sender_filter:
                search_criteria = f'(FROM "{self.config.email_sender_filter}")'
            
            status, messages = mail.search(None, search_criteria)
            if status != 'OK':
                self.log_error("Could not search emails")
                return items
            
            message_ids = messages[0].split()
            
            # Limit if specified
            if limit:
                message_ids = message_ids[-limit:]
            
            for msg_id in message_ids:
                try:
                    status, msg_data = mail.fetch(msg_id, '(RFC822)')
                    if status != 'OK':
                        continue
                    
                    raw_email = msg_data[0][1]
                    msg = email.message_from_bytes(raw_email)
                    
                    # Extract data
                    subject = self._decode_header_value(msg.get('Subject', ''))
                    from_addr = self._decode_header_value(msg.get('From', ''))
                    date_str = msg.get('Date', '')
                    message_id = self._get_message_id(msg)
                    
                    text_content, html_content = self._extract_text(msg)
                    
                    # Prefer HTML for links, but use text for content
                    if html_content:
                        clean_text = self._html_to_text(html_content)
                        links = self._extract_links(html_content)
                    else:
                        clean_text = text_content
                        links = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+', text_content)
                    
                    primary_link = self._find_primary_link(links, clean_text)
                    
                    # Parse date
                    try:
                        from email.utils import parsedate_to_datetime
                        published_at = parsedate_to_datetime(date_str)
                    except:
                        published_at = datetime.utcnow()
                    
                    items.append({
                        'message_id': message_id,
                        'title': subject,
                        'from': from_addr,
                        'content': clean_text,
                        'html': html_content,
                        'links': links,
                        'primary_link': primary_link,
                        'published_at': published_at,
                        'source_type': 'EMAIL',
                    })
                    
                except Exception as e:
                    self.log_error(f"Error processing email {msg_id}: {str(e)}")
                    continue
            
        except Exception as e:
            self.log_error(f"IMAP connection error: {str(e)}")
        
        finally:
            if mail:
                try:
                    mail.logout()
                except:
                    pass
        
        return items
    
    async def test_connection(self) -> bool:
        """Test IMAP connection"""
        try:
            mail = self._connect()
            folder = self.config.email_folder or settings.imap_folder
            status, _ = mail.select(folder)
            mail.logout()
            return status == 'OK'
        except Exception as e:
            self.log_error(f"Connection test failed: {str(e)}")
            return False

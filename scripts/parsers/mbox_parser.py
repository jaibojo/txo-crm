"""
.mbox Email Parser for Recruitment Sales Intelligence

Extracts:
- SPOCs and their email addresses
- Companies mentioned in conversations
- Conversation threads and timelines
- Funnel signals (stalled, proposals, JDs, etc.)
- Hidden opportunities (referrals, job changes, inbound mentions)
"""

import mailbox
import email
import re
from datetime import datetime
from collections import defaultdict
import pandas as pd
from email.utils import parsedate_to_datetime, parseaddr
import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging
logger = logging.getLogger(__name__)


class MboxParser:
    def __init__(self, config_path: str = "config/settings.yaml"):
        """Initialize parser with configuration."""
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        # Load classification keywords
        self.middle_funnel_keywords = self.config['classification']['middle_funnel']['keywords']
        self.hidden_opp_keywords = self.config['classification']['hidden_opportunities']

        # Storage for parsed data
        self.emails = []
        self.contacts = defaultdict(lambda: {
            'name': '',
            'email': '',
            'companies': set(),
            'roles': set(),
            'first_contact': None,
            'last_contact': None,
            'total_emails': 0,
            'inbound_count': 0,
            'outbound_count': 0,
        })

        self.conversations = defaultdict(lambda: {
            'thread_id': '',
            'participants': set(),
            'emails': [],
            'start_date': None,
            'last_date': None,
            'status': 'unknown',
            'signals': []
        })

    def parse_mbox(self, mbox_path: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Parse .mbox file and extract contacts, conversations, and signals.

        Returns:
            contacts_df: DataFrame of unique contacts
            conversations_df: DataFrame of conversation threads
            signals_df: DataFrame of funnel signals
        """
        logger.info(f"Starting to parse mbox file: {mbox_path}")

        mbox = mailbox.mbox(mbox_path)

        for idx, message in enumerate(mbox):
            try:
                self._process_message(message)

                if (idx + 1) % 100 == 0:
                    logger.info(f"Processed {idx + 1} emails...")

            except Exception as e:
                logger.error(f"Error processing email {idx}: {e}")
                continue

        logger.info(f"Completed parsing. Total emails: {len(self.emails)}")

        # Convert to DataFrames
        contacts_df = self._create_contacts_dataframe()
        conversations_df = self._create_conversations_dataframe()
        signals_df = self._create_signals_dataframe()

        return contacts_df, conversations_df, signals_df

    def _process_message(self, message):
        """Process individual email message."""
        # Extract basic metadata
        msg_id = message.get('Message-ID', '')
        subject = message.get('Subject', '')
        from_addr = message.get('From', '')
        to_addr = message.get('To', '')
        cc_addr = message.get('Cc', '')
        date = message.get('Date', '')
        in_reply_to = message.get('In-Reply-To', '')

        # Parse date
        try:
            email_date = parsedate_to_datetime(date)
        except:
            email_date = None

        # Extract body
        body = self._extract_body(message)

        # Parse sender and recipients
        from_name, from_email = parseaddr(from_addr)
        from_email = from_email.lower() if from_email else ''

        # Extract all recipients
        recipients = self._extract_recipients(to_addr, cc_addr)

        # Detect if this is inbound (to us) or outbound (from us)
        direction = self._detect_direction(from_email, recipients)

        # Extract company and role mentions
        companies = self._extract_companies(body + ' ' + subject)
        roles = self._extract_roles(body + ' ' + subject)

        # Update contact information
        self._update_contact(from_name, from_email, companies, roles, email_date, direction == 'inbound')

        for name, email_addr in recipients:
            self._update_contact(name, email_addr, companies, roles, email_date, direction == 'outbound')

        # Classify funnel stage and extract signals
        funnel_stage, signals = self._classify_email(subject, body)

        # Store email data
        email_data = {
            'msg_id': msg_id,
            'thread_id': in_reply_to if in_reply_to else msg_id,
            'subject': subject,
            'from_name': from_name,
            'from_email': from_email,
            'recipients': recipients,
            'date': email_date,
            'body': body,
            'direction': direction,
            'companies': list(companies),
            'roles': list(roles),
            'funnel_stage': funnel_stage,
            'signals': signals
        }

        self.emails.append(email_data)

        # Update conversation thread
        thread_id = in_reply_to if in_reply_to else msg_id
        self._update_conversation(thread_id, email_data)

    def _extract_body(self, message) -> str:
        """Extract email body text."""
        body = ""

        if message.is_multipart():
            for part in message.walk():
                content_type = part.get_content_type()

                if content_type == "text/plain":
                    try:
                        payload = part.get_payload(decode=True)
                        body += payload.decode('utf-8', errors='ignore')
                    except:
                        continue
        else:
            try:
                payload = message.get_payload(decode=True)
                body = payload.decode('utf-8', errors='ignore')
            except:
                body = str(message.get_payload())

        # Clean up body
        body = self._clean_text(body)
        return body

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove email signatures
        text = re.sub(r'--\s*\n.*', '', text, flags=re.DOTALL)
        return text.strip()

    def _extract_recipients(self, to_addr: str, cc_addr: str) -> List[Tuple[str, str]]:
        """Extract all recipients from To and Cc fields."""
        recipients = []

        for addr in [to_addr, cc_addr]:
            if not addr:
                continue

            # Split multiple addresses
            for item in addr.split(','):
                name, email_addr = parseaddr(item)
                if email_addr:
                    recipients.append((name, email_addr.lower()))

        return recipients

    def _detect_direction(self, from_email: str, recipients: List[Tuple[str, str]]) -> str:
        """Detect if email is inbound or outbound."""
        # Check if from our domain
        our_domains = ['talentxo.com', 'your-company.com']  # Update with actual domains

        from_domain = from_email.split('@')[-1] if '@' in from_email else ''

        if any(domain in from_domain for domain in our_domains):
            return 'outbound'
        else:
            return 'inbound'

    def _extract_companies(self, text: str) -> set:
        """Extract company names from text."""
        companies = set()

        # Common patterns for company mentions
        patterns = [
            r'\b([A-Z][a-zA-Z0-9\s&]+(?:Inc|LLC|Ltd|Corp|Corporation|Company|Technologies|Systems|Solutions|Services|Group))\b',
            r'\bat\s+([A-Z][a-zA-Z0-9\s&]{2,30})\b',
            r'\bfor\s+([A-Z][a-zA-Z0-9\s&]{2,30})\b',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text)
            companies.update([m.strip() for m in matches if len(m.strip()) > 3])

        return companies

    def _extract_roles(self, text: str) -> set:
        """Extract job role/position mentions from text."""
        roles = set()

        # Common role patterns
        role_keywords = [
            'engineer', 'developer', 'manager', 'director', 'analyst', 'designer',
            'architect', 'lead', 'senior', 'junior', 'consultant', 'specialist',
            'coordinator', 'administrator', 'officer', 'executive', 'VP', 'CTO',
            'CEO', 'CFO', 'COO', 'head of', 'recruiter', 'HR'
        ]

        # Match patterns like "looking for a [role]" or "hiring [role]"
        for keyword in role_keywords:
            pattern = rf'\b((?:senior|junior|lead)?\s*{keyword}(?:\s+\w+){{0,3}})\b'
            matches = re.findall(pattern, text, re.IGNORECASE)
            roles.update([m.strip() for m in matches])

        return roles

    def _update_contact(self, name: str, email: str, companies: set,
                       roles: set, date: datetime, is_inbound: bool):
        """Update contact information in the contacts dictionary."""
        if not email:
            return

        contact = self.contacts[email]

        if name and not contact['name']:
            contact['name'] = name

        contact['email'] = email
        contact['companies'].update(companies)
        contact['roles'].update(roles)
        contact['total_emails'] += 1

        if is_inbound:
            contact['inbound_count'] += 1
        else:
            contact['outbound_count'] += 1

        # Update dates
        if date:
            if not contact['first_contact'] or date < contact['first_contact']:
                contact['first_contact'] = date
            if not contact['last_contact'] or date > contact['last_contact']:
                contact['last_contact'] = date

    def _classify_email(self, subject: str, body: str) -> Tuple[str, List[str]]:
        """
        Classify email into funnel stage and extract signals.

        Returns:
            funnel_stage: 'bottom', 'middle', 'top', 'hidden_opportunity'
            signals: List of specific signals detected
        """
        text = (subject + ' ' + body).lower()
        signals = []

        # Check for middle funnel signals
        middle_signals = {
            'stalled': self.middle_funnel_keywords['stalled'],
            'jd_shared': self.middle_funnel_keywords['jd_shared'],
            'proposal_sent': self.middle_funnel_keywords['proposal_sent'],
            'negotiation': self.middle_funnel_keywords['negotiation'],
            'reconnect_later': self.middle_funnel_keywords['reconnect_later']
        }

        for signal_type, keywords in middle_signals.items():
            if any(keyword in text for keyword in keywords):
                signals.append(signal_type)

        # Check for hidden opportunity signals
        hidden_signals = {
            'inbound': self.hidden_opp_keywords['inbound_signals'],
            'referral': self.hidden_opp_keywords['referral_signals'],
            'job_change': self.hidden_opp_keywords['job_change_signals'],
            'keep_in_touch': self.hidden_opp_keywords['keep_in_touch']
        }

        for signal_type, keywords in hidden_signals.items():
            if any(keyword in text for keyword in keywords):
                signals.append(f'hidden_{signal_type}')

        # Determine funnel stage
        if any('hidden_' in s for s in signals):
            funnel_stage = 'hidden_opportunity'
        elif signals:
            funnel_stage = 'middle'
        else:
            funnel_stage = 'unknown'

        return funnel_stage, signals

    def _update_conversation(self, thread_id: str, email_data: dict):
        """Update conversation thread information."""
        conv = self.conversations[thread_id]

        conv['thread_id'] = thread_id
        conv['emails'].append(email_data['msg_id'])
        conv['participants'].add(email_data['from_email'])

        for _, recipient_email in email_data['recipients']:
            conv['participants'].add(recipient_email)

        # Update dates
        if email_data['date']:
            if not conv['start_date'] or email_data['date'] < conv['start_date']:
                conv['start_date'] = email_data['date']
            if not conv['last_date'] or email_data['date'] > conv['last_date']:
                conv['last_date'] = email_data['date']

        # Aggregate signals
        conv['signals'].extend(email_data['signals'])

    def _create_contacts_dataframe(self) -> pd.DataFrame:
        """Create DataFrame from contacts dictionary."""
        contacts_list = []

        for email, data in self.contacts.items():
            contacts_list.append({
                'email': email,
                'name': data['name'],
                'companies': ', '.join(data['companies']),
                'roles': ', '.join(data['roles']),
                'first_contact': data['first_contact'],
                'last_contact': data['last_contact'],
                'total_emails': data['total_emails'],
                'inbound_count': data['inbound_count'],
                'outbound_count': data['outbound_count'],
                'engagement_ratio': data['inbound_count'] / max(data['total_emails'], 1)
            })

        return pd.DataFrame(contacts_list)

    def _create_conversations_dataframe(self) -> pd.DataFrame:
        """Create DataFrame from conversations dictionary."""
        conv_list = []

        for thread_id, data in self.conversations.items():
            # Determine conversation status
            signals = data['signals']
            if 'stalled' in signals or 'reconnect_later' in signals:
                status = 'stalled'
            elif 'jd_shared' in signals or 'proposal_sent' in signals:
                status = 'active_but_not_closed'
            elif any('hidden_' in s for s in signals):
                status = 'hidden_opportunity'
            else:
                status = 'unknown'

            conv_list.append({
                'thread_id': thread_id,
                'participants': ', '.join(data['participants']),
                'participant_count': len(data['participants']),
                'email_count': len(data['emails']),
                'start_date': data['start_date'],
                'last_date': data['last_date'],
                'status': status,
                'signals': ', '.join(set(signals))
            })

        return pd.DataFrame(conv_list)

    def _create_signals_dataframe(self) -> pd.DataFrame:
        """Create DataFrame of all detected signals."""
        signals_list = []

        for email_data in self.emails:
            for signal in email_data['signals']:
                signals_list.append({
                    'msg_id': email_data['msg_id'],
                    'date': email_data['date'],
                    'from_email': email_data['from_email'],
                    'subject': email_data['subject'],
                    'signal_type': signal,
                    'funnel_stage': email_data['funnel_stage']
                })

        return pd.DataFrame(signals_list)


def main():
    """Main execution function."""
    parser = MboxParser()

    # Parse mbox file
    mbox_path = "data/raw/emails.mbox"
    contacts_df, conversations_df, signals_df = parser.parse_mbox(mbox_path)

    # Save outputs
    output_dir = Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)

    contacts_df.to_csv(output_dir / "email_contacts.csv", index=False)
    conversations_df.to_csv(output_dir / "email_conversations.csv", index=False)
    signals_df.to_csv(output_dir / "email_signals.csv", index=False)

    logger.info(f"Saved {len(contacts_df)} contacts")
    logger.info(f"Saved {len(conversations_df)} conversations")
    logger.info(f"Saved {len(signals_df)} signals")


if __name__ == "__main__":
    main()

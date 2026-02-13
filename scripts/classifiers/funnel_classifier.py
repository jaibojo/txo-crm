"""
Funnel Classification Engine

Segments all contacts into:
- 🟢 Bottom Funnel (active clients, past clients, dormant warm)
- 🟡 Middle Funnel (warm but not converted)
- 🔵 Hidden Opportunities (buried leads, job changes, referrals)
- ⚪ Top Funnel (cold leads, inbound not followed up)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import yaml
from pathlib import Path
import logging
logger = logging.getLogger(__name__)
# from fuzzywuzzy import fuzz  # Removed for simplicity


class FunnelClassifier:
    def __init__(self, config_path: str = "config/settings.yaml"):
        """Initialize classifier with configuration."""
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.classification_config = self.config['classification']
        self.scoring_config = self.config['scoring']

    def load_all_data(self, data_dir: str = "data/processed") -> Dict[str, pd.DataFrame]:
        """Load all processed data sources."""
        data_path = Path(data_dir)

        datasets = {}

        logger.info("Loading all data sources for classification...")

        # Database CSVs
        try:
            datasets['clients'] = pd.read_csv(data_path / "processed_clients.csv")
            logger.info(f"Loaded {len(datasets['clients'])} clients")
        except FileNotFoundError:
            logger.warning("processed_clients.csv not found")
            datasets['clients'] = pd.DataFrame()

        try:
            datasets['spocs'] = pd.read_csv(data_path / "processed_spocs.csv")
            logger.info(f"Loaded {len(datasets['spocs'])} SPOCs")
        except FileNotFoundError:
            logger.warning("processed_spocs.csv not found")
            datasets['spocs'] = pd.DataFrame()

        try:
            datasets['client_spoc_mapping'] = pd.read_csv(data_path / "client_spoc_mapping.csv")
            logger.info(f"Loaded {len(datasets['client_spoc_mapping'])} mappings")
        except FileNotFoundError:
            logger.warning("client_spoc_mapping.csv not found")
            datasets['client_spoc_mapping'] = pd.DataFrame()

        # Email data
        try:
            datasets['email_contacts'] = pd.read_csv(data_path / "email_contacts.csv")
            logger.info(f"Loaded {len(datasets['email_contacts'])} email contacts")
        except FileNotFoundError:
            logger.warning("email_contacts.csv not found")
            datasets['email_contacts'] = pd.DataFrame()

        try:
            datasets['email_conversations'] = pd.read_csv(data_path / "email_conversations.csv")
            logger.info(f"Loaded {len(datasets['email_conversations'])} conversations")
        except FileNotFoundError:
            logger.warning("email_conversations.csv not found")
            datasets['email_conversations'] = pd.DataFrame()

        try:
            datasets['email_signals'] = pd.read_csv(data_path / "email_signals.csv")
            logger.info(f"Loaded {len(datasets['email_signals'])} email signals")
        except FileNotFoundError:
            logger.warning("email_signals.csv not found")
            datasets['email_signals'] = pd.DataFrame()

        # LinkedIn enrichment
        try:
            enriched_path = Path("data/enriched")
            datasets['linkedin_enriched'] = pd.read_csv(enriched_path / "linkedin_enriched_spocs.csv")
            logger.info(f"Loaded {len(datasets['linkedin_enriched'])} LinkedIn-enriched profiles")
        except FileNotFoundError:
            logger.warning("linkedin_enriched_spocs.csv not found")
            datasets['linkedin_enriched'] = pd.DataFrame()

        return datasets

    def merge_and_deduplicate(self, datasets: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """
        Merge all data sources into unified contact list and deduplicate.

        Deduplication strategy:
        1. Match on email (exact)
        2. Match on LinkedIn URL (exact)
        3. Fuzzy match on name + company
        """
        logger.info("Merging and deduplicating contacts...")

        all_contacts = []

        # Extract contacts from client-SPOC mapping
        if not datasets['client_spoc_mapping'].empty:
            mapping_contacts = datasets['client_spoc_mapping'][[
                'email', 'full_name', 'company_name', 'job_title',
                'linkedin_url', 'client_status', 'client_value_score'
            ]].rename(columns={
                'full_name': 'name',
                'company_name': 'company',
                'job_title': 'title'
            })
            mapping_contacts['source'] = 'database'
            all_contacts.append(mapping_contacts)

        # Extract contacts from email data
        if not datasets['email_contacts'].empty:
            email_contacts = datasets['email_contacts'][[
                'email', 'name', 'companies', 'roles',
                'last_contact', 'engagement_ratio'
            ]].copy()

            # Take first company from list
            email_contacts['company'] = email_contacts['companies'].apply(
                lambda x: x.split(',')[0] if pd.notna(x) and x else None
            )

            # Take first role from list
            email_contacts['title'] = email_contacts['roles'].apply(
                lambda x: x.split(',')[0] if pd.notna(x) and x else None
            )

            email_contacts = email_contacts.drop(columns=['companies', 'roles'])
            email_contacts['source'] = 'email'
            all_contacts.append(email_contacts)

        # Extract LinkedIn enriched contacts
        if not datasets['linkedin_enriched'].empty:
            linkedin_contacts = datasets['linkedin_enriched'][[
                'email', 'full_name', 'current_company', 'current_title',
                'linkedin_url', 'job_change_detected'
            ]].rename(columns={
                'full_name': 'name',
                'current_company': 'company',
                'current_title': 'title'
            })
            linkedin_contacts['source'] = 'linkedin'
            all_contacts.append(linkedin_contacts)

        # Concatenate all contacts
        if not all_contacts:
            logger.warning("No contact data found!")
            return pd.DataFrame()

        combined = pd.concat(all_contacts, ignore_index=True, sort=False)

        logger.info(f"Combined {len(combined)} contact records from all sources")

        # Deduplicate
        deduplicated = self._deduplicate_contacts(combined)

        logger.info(f"After deduplication: {len(deduplicated)} unique contacts")

        return deduplicated

    def _deduplicate_contacts(self, df: pd.DataFrame) -> pd.DataFrame:
        """Deduplicate contacts using multiple matching strategies."""
        # Strategy 1: Exact email match
        df['email'] = df['email'].str.lower().str.strip()

        # For each email, keep the record with most complete data
        df['completeness_score'] = df.apply(self._calculate_completeness, axis=1)

        # Sort by completeness score (descending) and drop duplicates by email
        df_sorted = df.sort_values('completeness_score', ascending=False)
        deduplicated = df_sorted.drop_duplicates(subset=['email'], keep='first')

        return deduplicated

    def _calculate_completeness(self, row) -> int:
        """Calculate how complete a contact record is."""
        score = 0

        fields = ['email', 'name', 'company', 'title', 'linkedin_url']

        for field in fields:
            if field in row and pd.notna(row[field]) and row[field]:
                score += 1

        return score

    def classify_contacts(self, contacts_df: pd.DataFrame,
                         datasets: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """
        Classify each contact into funnel stage.

        Funnel stages:
        - bottom_active: Active clients
        - bottom_dormant_warm: Dormant but warm clients
        - middle_stalled: Conversation stalled
        - middle_jd_shared: JD shared but not closed
        - middle_proposal_sent: Proposal sent but no response
        - middle_negotiation: Negotiation stopped
        - middle_reconnect_later: Asked to reconnect later
        - hidden_inbound: Inbound lead not followed up
        - hidden_referral: Referral mention
        - hidden_job_change: HR changed company
        - hidden_keep_in_touch: Keep in touch thread
        - top_cold: Cold lead
        """
        logger.info("Classifying contacts into funnel stages...")

        # Initialize classification columns
        contacts_df['funnel_stage'] = 'unknown'
        contacts_df['funnel_signals'] = ''
        contacts_df['priority_score'] = 0

        # Create email to signals mapping
        email_signals_map = self._create_email_signals_map(datasets.get('email_signals', pd.DataFrame()))

        for idx, row in contacts_df.iterrows():
            email = row['email']

            # Determine funnel stage
            funnel_stage, signals = self._determine_funnel_stage(row, email_signals_map.get(email, []))

            contacts_df.at[idx, 'funnel_stage'] = funnel_stage
            contacts_df.at[idx, 'funnel_signals'] = ', '.join(signals)

            # Calculate priority score
            priority_score = self._calculate_priority_score(row, funnel_stage, signals)
            contacts_df.at[idx, 'priority_score'] = priority_score

        # Log classification results
        stage_counts = contacts_df['funnel_stage'].value_counts()
        logger.info("Classification results:")
        for stage, count in stage_counts.items():
            logger.info(f"  {stage}: {count}")

        return contacts_df

    def _create_email_signals_map(self, signals_df: pd.DataFrame) -> Dict[str, List[str]]:
        """Create mapping of email to detected signals."""
        email_signals = {}

        if signals_df.empty:
            return email_signals

        for _, row in signals_df.iterrows():
            email = row.get('from_email', '')
            signal = row.get('signal_type', '')

            if email and signal:
                if email not in email_signals:
                    email_signals[email] = []
                email_signals[email].append(signal)

        return email_signals

    def _determine_funnel_stage(self, row: pd.Series, signals: List[str]) -> Tuple[str, List[str]]:
        """Determine funnel stage for a contact based on available data and signals."""
        detected_signals = []

        # Check for bottom funnel indicators
        client_status = row.get('client_status', '')

        if client_status == 'active':
            return 'bottom_active', ['active_client']
        elif client_status == 'dormant_warm':
            return 'bottom_dormant_warm', ['dormant_warm_client']

        # Check for LinkedIn job change (hidden opportunity)
        if row.get('job_change_detected', False):
            detected_signals.append('job_change')
            return 'hidden_job_change', detected_signals

        # Check email signals for middle funnel
        if 'stalled' in signals:
            detected_signals.append('stalled')
            return 'middle_stalled', detected_signals

        if 'jd_shared' in signals:
            detected_signals.append('jd_shared')
            return 'middle_jd_shared', detected_signals

        if 'proposal_sent' in signals:
            detected_signals.append('proposal_sent')
            return 'middle_proposal_sent', detected_signals

        if 'negotiation' in signals:
            detected_signals.append('negotiation')
            return 'middle_negotiation', detected_signals

        if 'reconnect_later' in signals:
            detected_signals.append('reconnect_later')
            return 'middle_reconnect_later', detected_signals

        # Check for hidden opportunity signals
        if 'hidden_inbound' in signals:
            detected_signals.append('inbound_not_followed')
            return 'hidden_inbound', detected_signals

        if 'hidden_referral' in signals:
            detected_signals.append('referral_mention')
            return 'hidden_referral', detected_signals

        if 'hidden_keep_in_touch' in signals:
            detected_signals.append('keep_in_touch')
            return 'hidden_keep_in_touch', detected_signals

        # Default to top funnel (cold)
        return 'top_cold', []

    def _calculate_priority_score(self, row: pd.Series, funnel_stage: str, signals: List[str]) -> float:
        """
        Calculate priority score for a contact (0-100).

        Factors:
        - Recency (30%)
        - Relationship depth (25%)
        - Engagement level (20%)
        - Seniority (15%)
        - Company size (10%)
        """
        score = 0

        weights = self.scoring_config['weights']

        # 1. Recency (30 points)
        last_contact = row.get('last_contact')
        if pd.notna(last_contact):
            try:
                last_contact_date = pd.to_datetime(last_contact)
                days_since = (pd.Timestamp.now() - last_contact_date).days

                if days_since < 30:
                    score += weights['recency'] * 100
                elif days_since < 90:
                    score += weights['recency'] * 80
                elif days_since < 180:
                    score += weights['recency'] * 60
                elif days_since < 365:
                    score += weights['recency'] * 40
                else:
                    score += weights['recency'] * 20
            except:
                pass

        # 2. Relationship depth (25 points)
        client_value = row.get('client_value_score', 0)
        score += weights['relationship_depth'] * client_value

        # 3. Engagement level (20 points)
        engagement = row.get('engagement_ratio', 0)
        score += weights['engagement_level'] * engagement * 100

        # 4. Seniority bonus (15 points)
        title = str(row.get('title', '')).lower()
        seniority_score = 0

        if any(term in title for term in ['ceo', 'cto', 'cfo', 'coo', 'president', 'vp', 'director']):
            seniority_score = 100
        elif any(term in title for term in ['head', 'lead', 'manager', 'senior']):
            seniority_score = 70
        elif any(term in title for term in ['coordinator', 'specialist', 'analyst']):
            seniority_score = 40

        score += weights['seniority'] * seniority_score

        # 5. Funnel stage multiplier
        stage_multipliers = {
            'bottom_active': 1.5,
            'bottom_dormant_warm': 1.3,
            'hidden_job_change': 1.4,
            'middle_reconnect_later': 1.2,
            'middle_proposal_sent': 1.1,
            'hidden_referral': 1.2,
            'top_cold': 0.8
        }

        multiplier = stage_multipliers.get(funnel_stage, 1.0)
        score *= multiplier

        return min(score, 100)

    def segment_by_funnel(self, classified_df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """Segment classified contacts by funnel stage."""
        segments = {}

        # Bottom funnel
        segments['bottom_funnel'] = classified_df[
            classified_df['funnel_stage'].str.startswith('bottom')
        ].sort_values('priority_score', ascending=False)

        # Middle funnel
        segments['middle_funnel'] = classified_df[
            classified_df['funnel_stage'].str.startswith('middle')
        ].sort_values('priority_score', ascending=False)

        # Hidden opportunities
        segments['hidden_opportunities'] = classified_df[
            classified_df['funnel_stage'].str.startswith('hidden')
        ].sort_values('priority_score', ascending=False)

        # Top funnel
        segments['top_funnel'] = classified_df[
            classified_df['funnel_stage'].str.startswith('top')
        ].sort_values('priority_score', ascending=False)

        # Log segment sizes
        logger.info("Funnel segments:")
        for segment_name, segment_df in segments.items():
            logger.info(f"  {segment_name}: {len(segment_df)} contacts")

        return segments

    def save_classified_data(self, classified_df: pd.DataFrame,
                            segments: Dict[str, pd.DataFrame],
                            output_dir: str = "outputs/leads"):
        """Save classified and segmented data."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"Saving classified data to {output_dir}...")

        # Save master classified list
        classified_df.to_csv(output_path / "master_classified_contacts.csv", index=False)
        logger.info(f"Saved master list: {len(classified_df)} contacts")

        # Save individual segments
        for segment_name, segment_df in segments.items():
            filename = f"{segment_name}_contacts.csv"
            segment_df.to_csv(output_path / filename, index=False)
            logger.info(f"Saved {segment_name}: {len(segment_df)} contacts")


def main():
    """Main execution function."""
    classifier = FunnelClassifier()

    # Load all data
    datasets = classifier.load_all_data()

    # Merge and deduplicate
    unified_contacts = classifier.merge_and_deduplicate(datasets)

    # Classify contacts
    classified_contacts = classifier.classify_contacts(unified_contacts, datasets)

    # Segment by funnel
    segments = classifier.segment_by_funnel(classified_contacts)

    # Save results
    classifier.save_classified_data(classified_contacts, segments)

    logger.info("Classification complete!")


if __name__ == "__main__":
    main()

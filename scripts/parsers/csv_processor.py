"""
MySQL CSV Processor for Recruitment Sales Intelligence

Processes CSV exports from MySQL database:
- Clients data (1800+ clients)
- Roles/positions data
- SPOCs (points of contact)
- Interaction timelines
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple
import yaml
import logging
logger = logging.getLogger(__name__)


class MySQLCSVProcessor:
    def __init__(self, config_path: str = "config/settings.yaml"):
        """Initialize processor with configuration."""
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.clients_df = None
        self.roles_df = None
        self.spocs_df = None
        self.interactions_df = None

    def load_data(self, data_dir: str = "data/raw") -> None:
        """Load all CSV files from MySQL export."""
        data_path = Path(data_dir)

        logger.info("Loading MySQL CSV exports...")

        # Load each dataset
        try:
            self.clients_df = pd.read_csv(data_path / "clients.csv")
            logger.info(f"Loaded {len(self.clients_df)} clients")
        except FileNotFoundError:
            logger.warning("clients.csv not found")
            self.clients_df = pd.DataFrame()

        try:
            self.roles_df = pd.read_csv(data_path / "roles.csv")
            logger.info(f"Loaded {len(self.roles_df)} roles")
        except FileNotFoundError:
            logger.warning("roles.csv not found")
            self.roles_df = pd.DataFrame()

        try:
            self.spocs_df = pd.read_csv(data_path / "spocs.csv")
            logger.info(f"Loaded {len(self.spocs_df)} SPOCs")
        except FileNotFoundError:
            logger.warning("spocs.csv not found")
            self.spocs_df = pd.DataFrame()

        try:
            self.interactions_df = pd.read_csv(data_path / "interactions.csv")
            logger.info(f"Loaded {len(self.interactions_df)} interactions")
        except FileNotFoundError:
            logger.warning("interactions.csv not found")
            self.interactions_df = pd.DataFrame()

    def process_clients(self) -> pd.DataFrame:
        """
        Process clients data and classify by status.

        Expected columns in clients.csv:
        - client_id, company_name, industry, company_size, first_engagement_date,
          last_engagement_date, total_positions_filled, revenue_generated
        """
        if self.clients_df.empty:
            logger.warning("No clients data to process")
            return pd.DataFrame()

        logger.info("Processing clients data...")

        df = self.clients_df.copy()

        # Convert dates
        date_columns = ['first_engagement_date', 'last_engagement_date']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')

        # Calculate days since last engagement
        today = pd.Timestamp.now()
        if 'last_engagement_date' in df.columns:
            df['days_since_last_contact'] = (today - df['last_engagement_date']).dt.days
        else:
            df['days_since_last_contact'] = np.nan

        # Classify clients
        df['client_status'] = df.apply(self._classify_client_status, axis=1)

        # Calculate client value score
        df['client_value_score'] = df.apply(self._calculate_client_value, axis=1)

        # Identify dormant but warm accounts
        df['is_dormant_warm'] = df.apply(self._is_dormant_warm, axis=1)

        return df

    def _classify_client_status(self, row) -> str:
        """Classify client status based on engagement recency."""
        days_since = row.get('days_since_last_contact')

        if pd.isna(days_since):
            return 'unknown'

        active_threshold = self.config['classification']['bottom_funnel']['active_threshold_days']
        dormant_max = self.config['classification']['bottom_funnel']['dormant_max_days']

        if days_since <= active_threshold:
            return 'active'
        elif days_since <= dormant_max:
            return 'dormant_warm'
        else:
            return 'dormant_cold'

    def _calculate_client_value(self, row) -> float:
        """Calculate client value score (0-100)."""
        score = 0

        # Factor 1: Number of positions filled (max 40 points)
        positions = row.get('total_positions_filled', 0)
        score += min(positions * 2, 40)

        # Factor 2: Revenue generated (max 30 points)
        revenue = row.get('revenue_generated', 0)
        if revenue > 0:
            score += min(revenue / 10000, 30)  # Normalize based on revenue scale

        # Factor 3: Recency (max 30 points)
        days_since = row.get('days_since_last_contact', 999999)
        if days_since < 90:
            score += 30
        elif days_since < 180:
            score += 20
        elif days_since < 365:
            score += 10

        return min(score, 100)

    def _is_dormant_warm(self, row) -> bool:
        """Determine if client is dormant but warm (good reactivation target)."""
        days_since = row.get('days_since_last_contact')
        positions = row.get('total_positions_filled', 0)

        if pd.isna(days_since):
            return False

        dormant_min = self.config['classification']['bottom_funnel']['dormant_min_days']
        dormant_max = self.config['classification']['bottom_funnel']['dormant_max_days']

        # Dormant but had successful placements
        return (dormant_min <= days_since <= dormant_max and positions >= 1)

    def process_spocs(self) -> pd.DataFrame:
        """
        Process SPOCs (Single Points of Contact) data.

        Expected columns in spocs.csv:
        - spoc_id, client_id, full_name, email, phone, job_title,
          linkedin_url, first_contact_date, last_contact_date, is_active
        """
        if self.spocs_df.empty:
            logger.warning("No SPOCs data to process")
            return pd.DataFrame()

        logger.info("Processing SPOCs data...")

        df = self.spocs_df.copy()

        # Convert dates
        date_columns = ['first_contact_date', 'last_contact_date']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')

        # Calculate engagement metrics
        today = pd.Timestamp.now()
        if 'last_contact_date' in df.columns:
            df['days_since_last_contact'] = (today - df['last_contact_date']).dt.days
        else:
            df['days_since_last_contact'] = np.nan

        # Normalize email addresses
        if 'email' in df.columns:
            df['email'] = df['email'].str.lower().str.strip()

        # Extract domain from email
        if 'email' in df.columns:
            df['email_domain'] = df['email'].str.split('@').str[-1]

        return df

    def process_roles(self) -> pd.DataFrame:
        """
        Process roles/positions data.

        Expected columns in roles.csv:
        - role_id, client_id, job_title, job_description, seniority_level,
          department, posted_date, closed_date, status, salary_range
        """
        if self.roles_df.empty:
            logger.warning("No roles data to process")
            return pd.DataFrame()

        logger.info("Processing roles data...")

        df = self.roles_df.copy()

        # Convert dates
        date_columns = ['posted_date', 'closed_date']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')

        # Calculate time to fill
        if 'posted_date' in df.columns and 'closed_date' in df.columns:
            df['days_to_fill'] = (df['closed_date'] - df['posted_date']).dt.days

        # Categorize roles by seniority
        if 'seniority_level' in df.columns:
            df['role_category'] = df['seniority_level'].apply(self._categorize_role)

        return df

    def _categorize_role(self, seniority: str) -> str:
        """Categorize role by seniority level."""
        if pd.isna(seniority):
            return 'unknown'

        seniority_lower = str(seniority).lower()

        if any(term in seniority_lower for term in ['exec', 'c-level', 'vp', 'president']):
            return 'executive'
        elif any(term in seniority_lower for term in ['senior', 'lead', 'principal', 'director']):
            return 'senior'
        elif any(term in seniority_lower for term in ['mid', 'intermediate']):
            return 'mid'
        elif any(term in seniority_lower for term in ['junior', 'entry', 'associate']):
            return 'junior'
        else:
            return 'unknown'

    def process_interactions(self) -> pd.DataFrame:
        """
        Process interaction timeline data.

        Expected columns in interactions.csv:
        - interaction_id, client_id, spoc_id, interaction_date, interaction_type,
          notes, outcome, next_steps
        """
        if self.interactions_df.empty:
            logger.warning("No interactions data to process")
            return pd.DataFrame()

        logger.info("Processing interactions data...")

        df = self.interactions_df.copy()

        # Convert dates
        if 'interaction_date' in df.columns:
            df['interaction_date'] = pd.to_datetime(df['interaction_date'], errors='coerce')

        # Extract interaction patterns
        if 'notes' in df.columns:
            df['contains_jd'] = df['notes'].str.contains('job description|JD|requirement', case=False, na=False)
            df['contains_proposal'] = df['notes'].str.contains('proposal|quote|pricing', case=False, na=False)
            df['contains_negotiation'] = df['notes'].str.contains('budget|rate|negotiate', case=False, na=False)

        return df

    def create_client_spoc_mapping(self) -> pd.DataFrame:
        """
        Create comprehensive mapping of clients to SPOCs.

        Returns DataFrame with:
        - client_id, company_name, client_status
        - spoc_id, spoc_name, spoc_email, spoc_title, spoc_linkedin
        - relationship metrics
        """
        logger.info("Creating client-SPOC mapping...")

        # Merge clients and SPOCs
        if self.clients_df.empty or self.spocs_df.empty:
            logger.warning("Cannot create mapping without clients and SPOCs data")
            return pd.DataFrame()

        clients = self.process_clients()
        spocs = self.process_spocs()

        mapping = pd.merge(
            spocs,
            clients[['client_id', 'company_name', 'client_status', 'client_value_score', 'is_dormant_warm']],
            on='client_id',
            how='left'
        )

        return mapping

    def identify_cross_spoc_opportunities(self) -> pd.DataFrame:
        """
        Identify opportunities to reach different SPOCs at same company.

        Strategy: "We worked with [SPOC A], would like to connect with [SPOC B]"
        """
        logger.info("Identifying cross-SPOC opportunities...")

        mapping = self.create_client_spoc_mapping()

        if mapping.empty:
            return pd.DataFrame()

        # Group by company
        company_groups = mapping.groupby('company_name')

        opportunities = []

        for company, group in company_groups:
            if len(group) < 2:
                # Only one SPOC, no cross-SPOC opportunity
                continue

            spocs = group.to_dict('records')

            # Create opportunities for each SPOC to reference others
            for i, target_spoc in enumerate(spocs):
                past_spocs = [s for j, s in enumerate(spocs) if j != i]

                for past_spoc in past_spocs:
                    opportunities.append({
                        'strategy': 'cross_spoc_same_company',
                        'company_name': company,
                        'client_id': target_spoc.get('client_id'),
                        'target_spoc_name': target_spoc.get('full_name'),
                        'target_spoc_email': target_spoc.get('email'),
                        'target_spoc_title': target_spoc.get('job_title'),
                        'target_spoc_linkedin': target_spoc.get('linkedin_url'),
                        'reference_spoc_name': past_spoc.get('full_name'),
                        'reference_spoc_title': past_spoc.get('job_title'),
                        'client_status': target_spoc.get('client_status'),
                        'client_value_score': target_spoc.get('client_value_score'),
                        'priority': 'HIGH'
                    })

        return pd.DataFrame(opportunities)

    def identify_dormant_reactivation_targets(self) -> pd.DataFrame:
        """Identify dormant but warm clients for reactivation."""
        logger.info("Identifying dormant reactivation targets...")

        clients = self.process_clients()

        # Filter for dormant warm accounts
        dormant = clients[clients['is_dormant_warm'] == True].copy()

        # Sort by value score
        dormant = dormant.sort_values('client_value_score', ascending=False)

        return dormant

    def save_processed_data(self, output_dir: str = "data/processed"):
        """Save all processed data to CSV files."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"Saving processed data to {output_dir}...")

        # Process and save each dataset
        clients = self.process_clients()
        if not clients.empty:
            clients.to_csv(output_path / "processed_clients.csv", index=False)
            logger.info(f"Saved {len(clients)} processed clients")

        spocs = self.process_spocs()
        if not spocs.empty:
            spocs.to_csv(output_path / "processed_spocs.csv", index=False)
            logger.info(f"Saved {len(spocs)} processed SPOCs")

        roles = self.process_roles()
        if not roles.empty:
            roles.to_csv(output_path / "processed_roles.csv", index=False)
            logger.info(f"Saved {len(roles)} processed roles")

        interactions = self.process_interactions()
        if not interactions.empty:
            interactions.to_csv(output_path / "processed_interactions.csv", index=False)
            logger.info(f"Saved {len(interactions)} processed interactions")

        # Save strategic outputs
        mapping = self.create_client_spoc_mapping()
        if not mapping.empty:
            mapping.to_csv(output_path / "client_spoc_mapping.csv", index=False)
            logger.info(f"Saved {len(mapping)} client-SPOC mappings")

        cross_spoc_opps = self.identify_cross_spoc_opportunities()
        if not cross_spoc_opps.empty:
            cross_spoc_opps.to_csv(output_path / "cross_spoc_opportunities.csv", index=False)
            logger.info(f"Identified {len(cross_spoc_opps)} cross-SPOC opportunities")

        dormant = self.identify_dormant_reactivation_targets()
        if not dormant.empty:
            dormant.to_csv(output_path / "dormant_reactivation_targets.csv", index=False)
            logger.info(f"Identified {len(dormant)} dormant reactivation targets")


def main():
    """Main execution function."""
    processor = MySQLCSVProcessor()

    # Load data
    processor.load_data()

    # Process and save
    processor.save_processed_data()

    logger.info("CSV processing complete!")


if __name__ == "__main__":
    main()

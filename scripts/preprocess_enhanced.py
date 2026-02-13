"""
Enhanced preprocessing for TalentXO data with roles analysis.

Processes:
1. Txo Clientele (with verified status and repeat engagements)
2. All Roles (65k+ positions)
3. Sales Tracker data
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime


def process_txo_clientele():
    """Process Txo Clientele with verified status and repeat engagements."""
    print("Processing Txo Clientele...")

    df = pd.read_csv("data/raw/Strategy_Sourcing_Sales - Txo Clientele.csv")
    print(f"Loaded {len(df)} company records")

    # verified = 1 means confirmed client
    # Multiple rows for same company = repeat engagements

    # Group by company name to find repeat clients
    company_counts = df.groupby('name').size()
    repeat_clients = company_counts[company_counts > 1].index.tolist()

    print(f"  {len(company_counts)} unique companies")
    print(f"  {len(repeat_clients)} repeat clients (came back multiple times)")
    print(f"  {df['verified'].sum()} verified clients")

    # Create company master list
    companies = df.groupby('name').agg({
        'id': 'first',  # Take first ID
        'verified': 'max',  # If any row is verified, company is verified
        'cloned_from': 'first'
    }).reset_index()

    companies['is_repeat_client'] = companies['name'].isin(repeat_clients)
    companies['engagement_count'] = companies['name'].map(company_counts)

    return companies, df


def process_roles():
    """Process all roles data."""
    print("\nProcessing Roles...")

    # Read only essential columns to avoid CSV parsing issues
    usecols = ['id', 'title', 'datecreated', 'dateupdated', 'dateactivated',
               'activestatus', 'companyid']

    df = pd.read_csv("data/raw/txo_all_roles.csv",
                     usecols=usecols,
                     on_bad_lines='skip')
    print(f"Loaded {len(df)} roles")

    # Parse dates
    df['datecreated'] = pd.to_datetime(df['datecreated'], errors='coerce')
    df['dateupdated'] = pd.to_datetime(df['dateupdated'], errors='coerce')
    df['dateactivated'] = pd.to_datetime(df['dateactivated'], errors='coerce')

    # Active status (convert to int, handle any non-numeric values)
    df['activestatus'] = pd.to_numeric(df['activestatus'], errors='coerce').fillna(0).astype(int)
    print(f"  {df['activestatus'].sum()} active roles")
    print(f"  {len(df) - df['activestatus'].sum()} closed roles")

    return df


def link_roles_to_companies(companies_df, roles_df, clientele_df):
    """Link roles to companies and calculate metrics."""
    print("\nLinking roles to companies...")

    # Convert companyid to numeric
    roles_df['companyid'] = pd.to_numeric(roles_df['companyid'], errors='coerce')

    # Create mapping from companyid to company name
    company_map = clientele_df.set_index('id')['name'].to_dict()

    # Map company names to roles
    roles_df['company_name'] = roles_df['companyid'].map(company_map)

    # Report matching statistics
    matched = roles_df['company_name'].notna().sum()
    print(f"  Matched {matched} out of {len(roles_df)} roles to companies ({100*matched/len(roles_df):.1f}%)")

    # Calculate metrics per company
    company_metrics = roles_df.groupby('company_name').agg({
        'id': 'count',  # Total positions
        'activestatus': 'sum',  # Active positions
        'datecreated': ['min', 'max']  # First and last engagement
    }).reset_index()

    company_metrics.columns = [
        'company_name',
        'total_positions_filled',
        'active_positions',
        'first_engagement_date',
        'last_engagement_date'
    ]

    # Merge with companies
    enhanced_companies = companies_df.merge(
        company_metrics,
        left_on='name',
        right_on='company_name',
        how='left'
    )

    # Fill NaN values
    enhanced_companies['total_positions_filled'] = enhanced_companies['total_positions_filled'].fillna(0).astype(int)
    enhanced_companies['active_positions'] = enhanced_companies['active_positions'].fillna(0).astype(int)

    print(f"  Linked {enhanced_companies['total_positions_filled'].sum()} positions to companies")
    print(f"  Average positions per client: {enhanced_companies['total_positions_filled'].mean():.1f}")

    # Calculate days since last engagement
    today = pd.Timestamp.now()
    enhanced_companies['days_since_last_contact'] = (
        today - enhanced_companies['last_engagement_date']
    ).dt.days

    # Classify client status
    enhanced_companies['client_status'] = enhanced_companies.apply(
        lambda row: classify_client_status(row), axis=1
    )

    # Estimate revenue (assuming $10k per placement as baseline)
    enhanced_companies['revenue_generated'] = (
        enhanced_companies['total_positions_filled'] * 10000.0
    )

    return enhanced_companies, roles_df


def classify_client_status(row):
    """Classify client based on engagement recency."""
    days = row['days_since_last_contact']
    positions = row['total_positions_filled']

    if pd.isna(days):
        return 'unknown'

    if days < 180:  # Last 6 months
        return 'active'
    elif days < 730 and positions > 0:  # 6-24 months with history
        return 'dormant_warm'
    else:
        return 'dormant_cold'


def process_sales_tracker_spocs():
    """Extract SPOCs from Sales Tracker files."""
    print("\nProcessing Sales Tracker SPOCs...")

    all_spocs = []

    # From Clients Master
    try:
        master_df = pd.read_csv("data/raw/Sales Tracker - Clients - Master.csv")
        master_df.columns = master_df.columns.str.strip().str.lower().str.replace(' ', '_')

        spocs = master_df[['company_name', 'contact_name', 'department',
                          'contact_email', 'contact_number', 'date']].copy()
        spocs = spocs.dropna(subset=['contact_email'])
        all_spocs.append(spocs)
        print(f"  Extracted {len(spocs)} SPOCs from Clients Master")
    except Exception as e:
        print(f"  Could not load Clients Master: {e}")

    # From Client POC
    try:
        poc_df = pd.read_csv("data/raw/Sales Tracker - Client POC.csv")
        poc_df.columns = poc_df.columns.str.strip().str.lower().str.replace(' ', '_')

        spocs = poc_df[['company_name', 'contact_name', 'contact_email', 'date']].copy()
        spocs['department'] = None
        spocs['contact_number'] = None
        spocs = spocs.dropna(subset=['contact_email'])
        all_spocs.append(spocs)
        print(f"  Extracted {len(spocs)} SPOCs from Client POC")
    except Exception as e:
        print(f"  Could not load Client POC: {e}")

    # From New Leads
    try:
        leads_df = pd.read_csv("data/raw/Sales Tracker - New Leads.csv")
        leads_df.columns = leads_df.columns.str.strip().str.lower().str.replace(' ', '_')

        spocs = leads_df[['company_name', 'name', 'contact_email',
                         'contact_number', 'linkedin_url', 'date']].copy()
        spocs = spocs.rename(columns={'name': 'contact_name'})
        spocs['department'] = None
        spocs = spocs.dropna(subset=['contact_email'])
        all_spocs.append(spocs)
        print(f"  Extracted {len(spocs)} SPOCs from New Leads")
    except Exception as e:
        print(f"  Could not load New Leads: {e}")

    # Combine and deduplicate
    if all_spocs:
        combined = pd.concat(all_spocs, ignore_index=True, sort=False)
        combined['contact_email'] = combined['contact_email'].str.lower().str.strip()
        combined = combined.drop_duplicates(subset=['contact_email'], keep='first')
        print(f"  Total unique SPOCs: {len(combined)}")
        return combined
    else:
        return pd.DataFrame()


def create_final_outputs(enhanced_companies, roles_df, spocs_df):
    """Create standardized clients.csv and spocs.csv."""
    print("\nCreating final outputs...")

    # Clients CSV
    clients = pd.DataFrame({
        'client_id': enhanced_companies['id'],
        'company_name': enhanced_companies['name'],
        'industry': 'Various',  # Can be enriched later
        'company_size': 'Unknown',
        'first_engagement_date': enhanced_companies['first_engagement_date'],
        'last_engagement_date': enhanced_companies['last_engagement_date'],
        'total_positions_filled': enhanced_companies['total_positions_filled'],
        'revenue_generated': enhanced_companies['revenue_generated'],
        'verified': enhanced_companies['verified'],
        'is_repeat_client': enhanced_companies['is_repeat_client'],
        'engagement_count': enhanced_companies['engagement_count'],
        'active_positions': enhanced_companies['active_positions'],
        'days_since_last_contact': enhanced_companies['days_since_last_contact'],
        'client_status': enhanced_companies['client_status']
    })

    # SPOCs CSV
    # Create client_id mapping
    client_map = clients.set_index('company_name')['client_id'].to_dict()
    spocs_df['client_id'] = spocs_df['company_name'].map(client_map)

    # Handle missing mappings
    spocs_df['client_id'] = spocs_df['client_id'].fillna(0).astype(int)

    spocs = pd.DataFrame({
        'spoc_id': range(1, len(spocs_df) + 1),
        'client_id': spocs_df['client_id'],
        'full_name': spocs_df['contact_name'].fillna('Unknown'),
        'email': spocs_df['contact_email'],
        'phone': spocs_df['contact_number'].fillna(''),
        'job_title': spocs_df['department'].fillna(''),
        'linkedin_url': spocs_df.get('linkedin_url', '').fillna(''),
        'first_contact_date': pd.to_datetime(spocs_df['date'], format='%d/%m/%Y', errors='coerce'),
        'last_contact_date': pd.to_datetime(spocs_df['date'], format='%d/%m/%Y', errors='coerce'),
        'is_active': 1
    })

    # Roles CSV (optional but useful)
    roles = pd.DataFrame({
        'role_id': roles_df['id'],
        'client_id': roles_df['companyid'],
        'company_name': roles_df['company_name'],
        'job_title': roles_df['title'],
        'posted_date': roles_df['datecreated'],
        'updated_date': roles_df['dateupdated'],
        'activated_date': roles_df['dateactivated'],
        'status': roles_df['activestatus'].map({1: 'Active', 0: 'Closed'})
    })

    return clients, spocs, roles


def main():
    """Main execution."""
    print("=" * 80)
    print("ENHANCED TXO DATA PREPROCESSING")
    print("=" * 80)
    print()

    # 1. Process Txo Clientele
    companies_df, clientele_full = process_txo_clientele()

    # 2. Process Roles
    roles_df = process_roles()

    # 3. Link roles to companies
    enhanced_companies, enhanced_roles = link_roles_to_companies(
        companies_df, roles_df, clientele_full
    )

    # 4. Process SPOCs
    spocs_df = process_sales_tracker_spocs()

    # 5. Create final outputs
    clients, spocs, roles = create_final_outputs(
        enhanced_companies, enhanced_roles, spocs_df
    )

    # 6. Save to files
    output_dir = Path("data/raw")

    clients.to_csv(output_dir / "clients.csv", index=False)
    print(f"\n✅ Saved {len(clients)} clients to clients.csv")

    spocs.to_csv(output_dir / "spocs.csv", index=False)
    print(f"✅ Saved {len(spocs)} SPOCs to spocs.csv")

    roles.to_csv(output_dir / "roles.csv", index=False)
    print(f"✅ Saved {len(roles)} roles to roles.csv")

    # Print summary
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total Companies: {len(clients)}")
    print(f"  - Verified Clients: {clients['verified'].sum()}")
    print(f"  - Repeat Clients: {clients['is_repeat_client'].sum()}")
    print(f"  - Active (< 6 months): {(clients['client_status'] == 'active').sum()}")
    print(f"  - Dormant Warm (6-24 months): {(clients['client_status'] == 'dormant_warm').sum()}")
    print(f"  - Dormant Cold (> 24 months): {(clients['client_status'] == 'dormant_cold').sum()}")
    print()
    print(f"Total Positions: {len(roles)}")
    print(f"  - Active Positions: {(roles['status'] == 'Active').sum()}")
    print(f"  - Closed Positions: {(roles['status'] == 'Closed').sum()}")
    print()
    print(f"Total SPOCs: {len(spocs)}")
    print()
    print(f"Top 5 Clients by Positions:")
    top_clients = clients.nlargest(5, 'total_positions_filled')[
        ['company_name', 'total_positions_filled', 'revenue_generated', 'client_status']
    ]
    print(top_clients.to_string(index=False))
    print()
    print("=" * 80)
    print("Next step: python scripts/orchestrator.py")
    print("=" * 80)


if __name__ == "__main__":
    main()

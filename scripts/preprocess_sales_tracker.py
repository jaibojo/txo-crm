"""
Preprocess Sales Tracker CSV files into standard format.

Reads your custom Sales Tracker CSVs and creates:
- clients.csv (standardized)
- spocs.csv (standardized)
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
import numpy as np


def clean_column_names(df):
    """Standardize column names."""
    # Remove extra whitespace and convert to lowercase
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
    return df


def preprocess_clients_master():
    """Process 'Sales Tracker - Clients - Master.csv'"""
    print("Processing Clients Master...")

    df = pd.read_csv("data/raw/Sales Tracker - Clients - Master.csv")
    df = clean_column_names(df)

    print(f"Found {len(df)} records in Clients Master")
    print(f"Columns: {list(df.columns)}")

    # Extract unique companies for clients.csv
    clients = df[['company_name', 'date']].copy()
    clients = clients.dropna(subset=['company_name'])
    clients['company_name'] = clients['company_name'].str.strip()

    # Remove duplicates, keep first occurrence
    clients = clients.drop_duplicates(subset=['company_name'], keep='first')

    # Add required fields
    clients['client_id'] = range(1, len(clients) + 1)
    clients['industry'] = 'Various'  # You can categorize later
    clients['company_size'] = 'Unknown'
    clients['first_engagement_date'] = pd.to_datetime(clients['date'], format='%d/%m/%Y', errors='coerce')
    clients['last_engagement_date'] = clients['first_engagement_date']  # Will update later
    clients['total_positions_filled'] = 0  # Will calculate if you have roles data
    clients['revenue_generated'] = 0.0

    # Reorder columns
    clients = clients[['client_id', 'company_name', 'industry', 'company_size',
                      'first_engagement_date', 'last_engagement_date',
                      'total_positions_filled', 'revenue_generated']]

    print(f"Created {len(clients)} unique clients")

    return clients, df


def preprocess_spocs(clients_df, master_df):
    """Extract SPOCs from all contact sources."""
    print("\nProcessing SPOCs...")

    all_spocs = []

    # 1. From Clients Master
    print("Extracting from Clients Master...")
    spocs_master = master_df[['company_name', 'contact_name', 'department',
                               'contact_email', 'contact_number', 'date']].copy()
    spocs_master = spocs_master.dropna(subset=['contact_email'])
    spocs_master['source'] = 'clients_master'
    all_spocs.append(spocs_master)

    # 2. From Client POC
    try:
        print("Extracting from Client POC...")
        poc_df = pd.read_csv("data/raw/Sales Tracker - Client POC.csv")
        poc_df = clean_column_names(poc_df)
        spocs_poc = poc_df[['company_name', 'contact_name', 'contact_email', 'date']].copy()
        spocs_poc['department'] = None
        spocs_poc['contact_number'] = None
        spocs_poc['source'] = 'client_poc'
        all_spocs.append(spocs_poc)
    except Exception as e:
        print(f"Could not process Client POC: {e}")

    # 3. From New Leads
    try:
        print("Extracting from New Leads...")
        leads_df = pd.read_csv("data/raw/Sales Tracker - New Leads.csv")
        leads_df = clean_column_names(leads_df)
        spocs_leads = leads_df[['company_name', 'name', 'contact_email',
                                'contact_number', 'linkedin_url', 'date']].copy()
        spocs_leads = spocs_leads.rename(columns={'name': 'contact_name'})
        spocs_leads['department'] = None
        spocs_leads['source'] = 'new_leads'
        all_spocs.append(spocs_leads)
    except Exception as e:
        print(f"Could not process New Leads: {e}")

    # 4. From Txo Clientele
    try:
        print("Extracting from Txo Clientele...")
        txo_df = pd.read_csv("data/raw/Strategy_Sourcing_Sales - Txo Clientele.csv")
        txo_df = clean_column_names(txo_df)
        print(f"Txo Clientele columns: {list(txo_df.columns)}")

        # Check what columns are available
        available_cols = []
        if 'company_name' in txo_df.columns or 'company' in txo_df.columns:
            company_col = 'company_name' if 'company_name' in txo_df.columns else 'company'
            available_cols.append(company_col)

        if available_cols:
            spocs_txo = txo_df[available_cols].copy()
            if 'company' in spocs_txo.columns:
                spocs_txo = spocs_txo.rename(columns={'company': 'company_name'})
            spocs_txo['contact_name'] = None
            spocs_txo['contact_email'] = None
            spocs_txo['contact_number'] = None
            spocs_txo['department'] = None
            spocs_txo['date'] = None
            spocs_txo['source'] = 'txo_clientele'
            all_spocs.append(spocs_txo)
    except Exception as e:
        print(f"Could not process Txo Clientele: {e}")

    # Combine all SPOCs
    combined_spocs = pd.concat(all_spocs, ignore_index=True, sort=False)

    print(f"Combined {len(combined_spocs)} total SPOC records")

    # Clean up
    combined_spocs['contact_email'] = combined_spocs['contact_email'].str.lower().str.strip()

    # Remove duplicates (keep first occurrence)
    combined_spocs = combined_spocs.dropna(subset=['contact_email'])
    combined_spocs = combined_spocs.drop_duplicates(subset=['contact_email'], keep='first')

    print(f"After deduplication: {len(combined_spocs)} unique SPOCs")

    # Create client_id mapping
    client_map = clients_df.set_index('company_name')['client_id'].to_dict()
    combined_spocs['client_id'] = combined_spocs['company_name'].map(client_map)

    # Fill in missing client_ids (for new companies not in clients.csv)
    missing_companies = combined_spocs[combined_spocs['client_id'].isna()]['company_name'].unique()
    if len(missing_companies) > 0:
        print(f"Found {len(missing_companies)} new companies in SPOCs, adding to clients...")

        # Add new clients
        max_id = clients_df['client_id'].max()
        for i, company in enumerate(missing_companies):
            if pd.notna(company):
                combined_spocs.loc[combined_spocs['company_name'] == company, 'client_id'] = max_id + i + 1

    # Create standardized SPOC dataframe
    spocs = pd.DataFrame({
        'spoc_id': range(1, len(combined_spocs) + 1),
        'client_id': combined_spocs['client_id'].fillna(0).astype(int),
        'full_name': combined_spocs['contact_name'].fillna('Unknown'),
        'email': combined_spocs['contact_email'],
        'phone': combined_spocs['contact_number'].fillna(''),
        'job_title': combined_spocs['department'].fillna(''),
        'linkedin_url': combined_spocs.get('linkedin_url', '').fillna(''),
        'first_contact_date': pd.to_datetime(combined_spocs['date'], format='%d/%m/%Y', errors='coerce'),
        'last_contact_date': pd.to_datetime(combined_spocs['date'], format='%d/%m/%Y', errors='coerce'),
        'is_active': 1
    })

    return spocs


def main():
    """Main preprocessing function."""
    print("=" * 80)
    print("SALES TRACKER DATA PREPROCESSING")
    print("=" * 80)
    print()

    # Process clients
    clients_df, master_df = preprocess_clients_master()

    # Process SPOCs
    spocs_df = preprocess_spocs(clients_df, master_df)

    # Save to standard filenames
    output_dir = Path("data/raw")

    clients_df.to_csv(output_dir / "clients.csv", index=False)
    print(f"\n✅ Saved {len(clients_df)} clients to clients.csv")

    spocs_df.to_csv(output_dir / "spocs.csv", index=False)
    print(f"✅ Saved {len(spocs_df)} SPOCs to spocs.csv")

    # Print summary
    print()
    print("=" * 80)
    print("PREPROCESSING COMPLETE!")
    print("=" * 80)
    print()
    print("Summary:")
    print(f"  Clients: {len(clients_df)}")
    print(f"  SPOCs: {len(spocs_df)}")
    print()
    print("Next step:")
    print("  python scripts/validate_data.py")
    print()


if __name__ == "__main__":
    main()

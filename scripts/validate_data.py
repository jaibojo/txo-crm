"""
Data Validation Script

Run this BEFORE executing the pipeline to verify your data files are correct.

Usage:
    python scripts/validate_data.py
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple
import sys


class DataValidator:
    def __init__(self):
        self.data_dir = Path("data/raw")
        self.errors = []
        self.warnings = []
        self.info = []

    def validate_all(self) -> bool:
        """Validate all data sources. Returns True if valid, False otherwise."""
        print("=" * 80)
        print("DATA VALIDATION CHECK")
        print("=" * 80)
        print()

        # Check if data directory exists
        if not self.data_dir.exists():
            self.errors.append(f"Data directory not found: {self.data_dir}")
            self.print_results()
            return False

        # Validate each data source
        self.validate_clients_csv()
        self.validate_spocs_csv()
        self.validate_roles_csv()
        self.validate_interactions_csv()
        self.validate_mbox()

        # Print results
        self.print_results()

        # Return overall status
        return len(self.errors) == 0

    def validate_clients_csv(self):
        """Validate clients.csv file."""
        filepath = self.data_dir / "clients.csv"

        if not filepath.exists():
            self.errors.append("❌ clients.csv NOT FOUND (required)")
            return

        try:
            df = pd.read_csv(filepath)

            # Check required columns
            required_cols = [
                'client_id', 'company_name', 'first_engagement_date',
                'last_engagement_date'
            ]

            missing_cols = [col for col in required_cols if col not in df.columns]

            if missing_cols:
                self.errors.append(f"❌ clients.csv missing columns: {missing_cols}")
            else:
                self.info.append(f"✅ clients.csv - {len(df)} records, all required columns present")

            # Check for empty values
            for col in required_cols:
                if col in df.columns:
                    null_count = df[col].isna().sum()
                    if null_count > 0:
                        self.warnings.append(f"⚠️  clients.csv: {null_count} null values in '{col}'")

            # Check date formats
            for date_col in ['first_engagement_date', 'last_engagement_date']:
                if date_col in df.columns:
                    try:
                        pd.to_datetime(df[date_col], errors='coerce')
                    except Exception as e:
                        self.warnings.append(f"⚠️  clients.csv: Invalid date format in '{date_col}'")

            # Check for recommended columns
            recommended_cols = ['total_positions_filled', 'revenue_generated', 'industry']
            missing_recommended = [col for col in recommended_cols if col not in df.columns]

            if missing_recommended:
                self.warnings.append(f"⚠️  clients.csv: Recommended columns missing: {missing_recommended}")

        except Exception as e:
            self.errors.append(f"❌ Error reading clients.csv: {e}")

    def validate_spocs_csv(self):
        """Validate spocs.csv file."""
        filepath = self.data_dir / "spocs.csv"

        if not filepath.exists():
            self.errors.append("❌ spocs.csv NOT FOUND (required)")
            return

        try:
            df = pd.read_csv(filepath)

            # Check required columns
            required_cols = [
                'spoc_id', 'client_id', 'full_name', 'email'
            ]

            missing_cols = [col for col in required_cols if col not in df.columns]

            if missing_cols:
                self.errors.append(f"❌ spocs.csv missing columns: {missing_cols}")
            else:
                self.info.append(f"✅ spocs.csv - {len(df)} records, all required columns present")

            # Check email format
            if 'email' in df.columns:
                # Basic email validation
                invalid_emails = df[~df['email'].astype(str).str.contains('@', na=False)]
                if len(invalid_emails) > 0:
                    self.warnings.append(f"⚠️  spocs.csv: {len(invalid_emails)} records with invalid email format")

                # Check for duplicate emails
                duplicate_emails = df[df['email'].duplicated()]
                if len(duplicate_emails) > 0:
                    self.warnings.append(f"⚠️  spocs.csv: {len(duplicate_emails)} duplicate email addresses found")

            # Check for recommended columns
            recommended_cols = ['job_title', 'linkedin_url', 'last_contact_date']
            missing_recommended = [col for col in recommended_cols if col not in df.columns]

            if missing_recommended:
                self.warnings.append(f"⚠️  spocs.csv: Recommended columns missing: {missing_recommended}")

            # Check client_id linkage
            if 'client_id' in df.columns:
                clients_path = self.data_dir / "clients.csv"
                if clients_path.exists():
                    clients_df = pd.read_csv(clients_path)
                    if 'client_id' in clients_df.columns:
                        # Check for orphaned SPOCs
                        orphaned = df[~df['client_id'].isin(clients_df['client_id'])]
                        if len(orphaned) > 0:
                            self.warnings.append(f"⚠️  spocs.csv: {len(orphaned)} SPOCs have client_id not in clients.csv")

        except Exception as e:
            self.errors.append(f"❌ Error reading spocs.csv: {e}")

    def validate_roles_csv(self):
        """Validate roles.csv file (optional)."""
        filepath = self.data_dir / "roles.csv"

        if not filepath.exists():
            self.info.append("ℹ️  roles.csv NOT FOUND (optional - skipping)")
            return

        try:
            df = pd.read_csv(filepath)

            # Check recommended columns
            recommended_cols = [
                'role_id', 'client_id', 'job_title', 'posted_date', 'status'
            ]

            missing_cols = [col for col in recommended_cols if col not in df.columns]

            if missing_cols:
                self.warnings.append(f"⚠️  roles.csv: Missing columns: {missing_cols}")
            else:
                self.info.append(f"✅ roles.csv - {len(df)} records found")

        except Exception as e:
            self.warnings.append(f"⚠️  Error reading roles.csv: {e}")

    def validate_interactions_csv(self):
        """Validate interactions.csv file (optional)."""
        filepath = self.data_dir / "interactions.csv"

        if not filepath.exists():
            self.info.append("ℹ️  interactions.csv NOT FOUND (optional - skipping)")
            return

        try:
            df = pd.read_csv(filepath)

            # Check recommended columns
            recommended_cols = [
                'interaction_id', 'client_id', 'interaction_date', 'notes'
            ]

            missing_cols = [col for col in recommended_cols if col not in df.columns]

            if missing_cols:
                self.warnings.append(f"⚠️  interactions.csv: Missing columns: {missing_cols}")
            else:
                self.info.append(f"✅ interactions.csv - {len(df)} records found")

        except Exception as e:
            self.warnings.append(f"⚠️  Error reading interactions.csv: {e}")

    def validate_mbox(self):
        """Validate .mbox email archive."""
        # Check for any .mbox file
        mbox_files = list(self.data_dir.glob("*.mbox"))

        if not mbox_files:
            self.errors.append("❌ No .mbox file found in data/raw/ (required)")
            return

        if len(mbox_files) > 1:
            self.warnings.append(f"⚠️  Multiple .mbox files found. Will use: {mbox_files[0].name}")

        mbox_file = mbox_files[0]

        # Check file size
        size_mb = mbox_file.stat().st_size / (1024 * 1024)

        if size_mb < 0.1:
            self.warnings.append(f"⚠️  {mbox_file.name} is very small ({size_mb:.1f} MB) - might be empty?")
        elif size_mb > 5000:
            self.warnings.append(f"⚠️  {mbox_file.name} is very large ({size_mb:.0f} MB) - processing may take time")
        else:
            self.info.append(f"✅ {mbox_file.name} found ({size_mb:.1f} MB)")

    def print_results(self):
        """Print validation results."""
        print()
        print("=" * 80)
        print("VALIDATION RESULTS")
        print("=" * 80)
        print()

        # Print errors
        if self.errors:
            print("🔴 ERRORS (Must fix before running pipeline):")
            print("-" * 80)
            for error in self.errors:
                print(f"  {error}")
            print()

        # Print warnings
        if self.warnings:
            print("🟡 WARNINGS (Recommended to fix, but pipeline will run):")
            print("-" * 80)
            for warning in self.warnings:
                print(f"  {warning}")
            print()

        # Print info
        if self.info:
            print("🟢 INFO:")
            print("-" * 80)
            for info in self.info:
                print(f"  {info}")
            print()

        # Summary
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Errors:   {len(self.errors)}")
        print(f"Warnings: {len(self.warnings)}")
        print()

        if len(self.errors) == 0:
            print("✅ VALIDATION PASSED - Ready to run pipeline!")
            print()
            print("Next step:")
            print("  python scripts/orchestrator.py")
        else:
            print("❌ VALIDATION FAILED - Fix errors before running pipeline")
            print()
            print("Tips:")
            print("  1. Check docs/schema.md for expected file format")
            print("  2. Look at data/raw/SAMPLE_*.csv for examples")
            print("  3. Ensure CSV column names match exactly")

        print("=" * 80)


def main():
    """Main execution."""
    validator = DataValidator()
    success = validator.validate_all()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

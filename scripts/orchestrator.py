"""
Main Orchestrator for Recruitment Sales Intelligence Pipeline

Coordinates all data processing steps:
1. Parse .mbox emails
2. Process MySQL CSV exports
3. Enrich with LinkedIn data (optional)
4. Classify into funnel stages
5. Generate outreach templates
6. Export CRM-ready leads
"""

import sys
from pathlib import Path
import yaml
import logging
from datetime import datetime

# Setup simple logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('outputs/reports/processing.log')
    ]
)
logger = logging.getLogger(__name__)

# Add scripts directory to path
sys.path.append(str(Path(__file__).parent))

from parsers.mbox_parser import MboxParser
from parsers.csv_processor import MySQLCSVProcessor
from classifiers.funnel_classifier import FunnelClassifier


class SalesIntelligenceOrchestrator:
    def __init__(self, config_path: str = "config/settings.yaml"):
        """Initialize orchestrator."""
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        logger.info("=" * 80)
        logger.info("Sales Intelligence Pipeline Started")
        logger.info(f"Timestamp: {datetime.now()}")
        logger.info("=" * 80)

    def run_pipeline(self, skip_linkedin: bool = True):
        """
        Run the complete data processing pipeline.

        Args:
            skip_linkedin: Skip LinkedIn enrichment (requires manual setup and credentials)
        """
        try:
            # Step 1: Parse .mbox emails
            logger.info("\n" + "=" * 80)
            logger.info("STEP 1: Parsing Email Archive (.mbox)")
            logger.info("=" * 80)
            self.parse_emails()

            # Step 2: Process MySQL CSV exports
            logger.info("\n" + "=" * 80)
            logger.info("STEP 2: Processing MySQL CSV Exports")
            logger.info("=" * 80)
            self.process_database_csvs()

            # Step 3: LinkedIn enrichment (optional)
            if not skip_linkedin:
                logger.info("\n" + "=" * 80)
                logger.info("STEP 3: LinkedIn Profile Enrichment")
                logger.info("=" * 80)
                self.enrich_linkedin_data()
            else:
                logger.info("\n" + "=" * 80)
                logger.info("STEP 3: LinkedIn Enrichment SKIPPED")
                logger.info("=" * 80)

            # Step 4: Classify and segment
            logger.info("\n" + "=" * 80)
            logger.info("STEP 4: Classifying Contacts into Funnels")
            logger.info("=" * 80)
            self.classify_and_segment()

            # Step 5: Generate strategic outputs
            logger.info("\n" + "=" * 80)
            logger.info("STEP 5: Generating Strategic Outputs")
            logger.info("=" * 80)
            self.generate_strategic_outputs()

            # Step 6: Generate outreach templates
            logger.info("\n" + "=" * 80)
            logger.info("STEP 6: Generating Outreach Templates")
            logger.info("=" * 80)
            self.generate_templates()

            # Summary report
            logger.info("\n" + "=" * 80)
            logger.info("Pipeline Complete!")
            logger.info("=" * 80)
            self.generate_summary_report()

        except Exception as e:
            logger.error(f"Pipeline failed with error: {e}")
            raise

    def parse_emails(self):
        """Parse .mbox email archive."""
        mbox_path = self.config['data_sources']['email']['mbox_file']

        if not Path(mbox_path).exists():
            logger.warning(f".mbox file not found: {mbox_path}")
            logger.warning("Skipping email parsing. Upload your .mbox file and try again.")
            return

        parser = MboxParser()

        contacts_df, conversations_df, signals_df = parser.parse_mbox(mbox_path)

        # Save outputs
        output_dir = Path("data/processed")
        output_dir.mkdir(parents=True, exist_ok=True)

        contacts_df.to_csv(output_dir / "email_contacts.csv", index=False)
        conversations_df.to_csv(output_dir / "email_conversations.csv", index=False)
        signals_df.to_csv(output_dir / "email_signals.csv", index=False)

        logger.info(f"✓ Parsed {len(contacts_df)} unique email contacts")
        logger.info(f"✓ Identified {len(conversations_df)} conversation threads")
        logger.info(f"✓ Detected {len(signals_df)} funnel signals")

    def process_database_csvs(self):
        """Process MySQL database CSV exports."""
        processor = MySQLCSVProcessor()

        # Check if data files exist
        data_dir = Path("data/raw")
        required_files = ['clients.csv', 'spocs.csv']

        missing_files = [f for f in required_files if not (data_dir / f).exists()]

        if missing_files:
            logger.warning(f"Missing CSV files: {missing_files}")
            logger.warning("Upload your MySQL exports to data/raw/ and try again.")
            return

        # Load and process
        processor.load_data()
        processor.save_processed_data()

        logger.info("✓ Database CSVs processed successfully")

    def enrich_linkedin_data(self):
        """
        Enrich contacts with LinkedIn data.

        NOTE: This step requires:
        1. LinkedIn credentials (set as environment variables)
        2. Manual monitoring for CAPTCHAs
        3. Compliance with LinkedIn ToS
        """
        logger.warning("LinkedIn enrichment requires manual setup!")
        logger.info("Run scripts/enrichers/linkedin_enricher.py separately with proper credentials")
        logger.info("For now, proceeding without LinkedIn data...")

    def classify_and_segment(self):
        """Classify contacts into funnel stages and segment."""
        classifier = FunnelClassifier()

        # Load all processed data
        datasets = classifier.load_all_data()

        # Merge and deduplicate
        unified_contacts = classifier.merge_and_deduplicate(datasets)

        logger.info(f"✓ Unified {len(unified_contacts)} unique contacts")

        # Classify
        classified_contacts = classifier.classify_contacts(unified_contacts, datasets)

        # Segment
        segments = classifier.segment_by_funnel(classified_contacts)

        # Save
        classifier.save_classified_data(classified_contacts, segments)

        logger.info("✓ Classification and segmentation complete")

    def generate_strategic_outputs(self):
        """Generate strategic opportunity reports."""
        processor = MySQLCSVProcessor()
        processor.load_data("data/processed")

        output_dir = Path("outputs/leads")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Cross-SPOC opportunities
        try:
            cross_spoc_opps = processor.identify_cross_spoc_opportunities()
            if not cross_spoc_opps.empty:
                cross_spoc_opps.to_csv(output_dir / "cross_spoc_opportunities.csv", index=False)
                logger.info(f"✓ Identified {len(cross_spoc_opps)} cross-SPOC opportunities")
        except Exception as e:
            logger.warning(f"Could not generate cross-SPOC opportunities: {e}")

        # Dormant reactivation targets
        try:
            dormant = processor.identify_dormant_reactivation_targets()
            if not dormant.empty:
                dormant.to_csv(output_dir / "dormant_reactivation_targets.csv", index=False)
                logger.info(f"✓ Identified {len(dormant)} dormant reactivation targets")
        except Exception as e:
            logger.warning(f"Could not generate dormant targets: {e}")

    def generate_templates(self):
        """Generate outreach email templates."""
        logger.info("Generating personalized outreach templates...")

        templates_dir = Path("outputs/templates")
        templates_dir.mkdir(parents=True, exist_ok=True)

        # Template 1: Cross-SPOC (Same Company)
        cross_spoc_template = """Subject: Following up - worked with {reference_spoc_name}

Hi {target_spoc_name},

I hope this email finds you well. I'm reaching out because we've had the pleasure of working with {reference_spoc_name} ({reference_spoc_title}) at {company_name} on several successful placements over the past {timeframe}.

Given our proven track record with {company_name}, I wanted to introduce our services to you and explore if we could support your hiring needs in {department/function}.

Would you be open to a brief call to discuss how we might be able to help?

Best regards,
[Your Name]
TalentXO
"""

        with open(templates_dir / "cross_spoc_template.txt", 'w') as f:
            f.write(cross_spoc_template)

        # Template 2: SPOC at New Company
        new_company_template = """Subject: Great to see you at {new_company_name}!

Hi {spoc_name},

I hope you're doing well! I saw that you've recently joined {new_company_name} as {new_title} - congratulations!

We had a great working relationship when you were at {old_company_name}, and I'd love to see if we could support your hiring needs at {new_company_name}.

Since we last worked together, we've:
- Grown our team to {team_size}
- Expanded into {new_domains}
- Filled {number}+ positions across {industries}

Would you be open to reconnecting? I'd love to hear about your goals at {new_company_name} and explore how we can help.

Best regards,
[Your Name]
TalentXO
"""

        with open(templates_dir / "spoc_new_company_template.txt", 'w') as f:
            f.write(new_company_template)

        # Template 3: Reverse Referral
        reverse_referral_template = """Subject: Quick request - referral to {old_company_name}

Hi {spoc_name},

Hope all is well at {new_company_name}!

Since you've moved on from {old_company_name}, I wanted to ask if you could introduce us to your replacement or the current hiring manager there.

We had great success working together on {roles_worked}, and I'd love to continue that relationship with your former team.

Would you be comfortable making an introduction?

Thanks so much!

Best regards,
[Your Name]
TalentXO
"""

        with open(templates_dir / "reverse_referral_template.txt", 'w') as f:
            f.write(reverse_referral_template)

        # Template 4: Middle Funnel Re-engagement
        middle_funnel_template = """Subject: Re: {previous_subject} - checking back in

Hi {spoc_name},

I wanted to follow up on our conversation from {last_contact_date} about {topic}.

I know timing wasn't right back then, but I wanted to reconnect because:

Since we last spoke, we've:
- {growth_metric_1}
- {growth_metric_2}
- {growth_metric_3}

Given these improvements and your {season/quarter} planning, would it make sense to revisit the conversation?

Happy to jump on a quick call if you're open to it.

Best regards,
[Your Name]
TalentXO
"""

        with open(templates_dir / "middle_funnel_bump_template.txt", 'w') as f:
            f.write(middle_funnel_template)

        logger.info(f"✓ Generated 4 outreach templates in {templates_dir}")

    def generate_summary_report(self):
        """Generate final summary report."""
        import pandas as pd

        reports_dir = Path("outputs/reports")
        reports_dir.mkdir(parents=True, exist_ok=True)

        # Load all outputs
        leads_dir = Path("outputs/leads")

        summary = []

        summary.append("=" * 80)
        summary.append("SALES INTELLIGENCE PIPELINE - SUMMARY REPORT")
        summary.append(f"Generated: {datetime.now()}")
        summary.append("=" * 80)
        summary.append("")

        # Funnel segments
        summary.append("📊 FUNNEL BREAKDOWN")
        summary.append("-" * 80)

        segments = {
            'Bottom Funnel': 'bottom_funnel_contacts.csv',
            'Middle Funnel': 'middle_funnel_contacts.csv',
            'Hidden Opportunities': 'hidden_opportunities_contacts.csv',
            'Top Funnel': 'top_funnel_contacts.csv'
        }

        for segment_name, filename in segments.items():
            filepath = leads_dir / filename
            if filepath.exists():
                df = pd.read_csv(filepath)
                summary.append(f"  {segment_name}: {len(df)} contacts")

        summary.append("")

        # Strategic opportunities
        summary.append("🎯 STRATEGIC OPPORTUNITIES")
        summary.append("-" * 80)

        opportunities = {
            'Cross-SPOC (Same Company)': 'cross_spoc_opportunities.csv',
            'Dormant Reactivation Targets': 'dormant_reactivation_targets.csv',
            'Job Change Opportunities': 'job_change_opportunities.csv'
        }

        for opp_name, filename in opportunities.items():
            filepath = leads_dir / filename
            if filepath.exists():
                df = pd.read_csv(filepath)
                summary.append(f"  {opp_name}: {len(df)} opportunities")

        summary.append("")

        # Top priority contacts
        summary.append("⭐ TOP 10 PRIORITY CONTACTS")
        summary.append("-" * 80)

        master_file = leads_dir / "master_classified_contacts.csv"
        if master_file.exists():
            master_df = pd.read_csv(master_file)
            top_10 = master_df.nlargest(10, 'priority_score')[['name', 'company', 'funnel_stage', 'priority_score']]

            for idx, row in top_10.iterrows():
                summary.append(f"  {row['name']} @ {row['company']} - {row['funnel_stage']} (Score: {row['priority_score']:.1f})")

        summary.append("")
        summary.append("=" * 80)
        summary.append("NEXT STEPS:")
        summary.append("=" * 80)
        summary.append("1. Review outputs/leads/ for segmented contact lists")
        summary.append("2. Use outputs/templates/ for personalized outreach")
        summary.append("3. Import master_classified_contacts.csv into your CRM")
        summary.append("4. Prioritize high-score contacts for immediate outreach")
        summary.append("")

        # Print to console
        report_text = "\n".join(summary)
        print("\n" + report_text)

        # Save to file
        with open(reports_dir / "pipeline_summary.txt", 'w') as f:
            f.write(report_text)

        logger.info(f"✓ Summary report saved to {reports_dir / 'pipeline_summary.txt'}")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Recruitment Sales Intelligence Pipeline")
    parser.add_argument('--with-linkedin', action='store_true',
                       help='Include LinkedIn enrichment (requires manual setup)')

    args = parser.parse_args()

    orchestrator = SalesIntelligenceOrchestrator()

    orchestrator.run_pipeline(skip_linkedin=not args.with_linkedin)


if __name__ == "__main__":
    main()

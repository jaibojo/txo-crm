"""
LinkedIn Profile Enrichment Tool

Finds current companies, job titles, and profile links for SPOCs.

IMPORTANT: This uses web scraping which may violate LinkedIn's Terms of Service.
Use responsibly and consider:
1. Using LinkedIn's official API if you have access
2. Using Sales Navigator exports
3. Using third-party enrichment services (Apollo, ZoomInfo, etc.)
4. Manual research for high-value targets

This script is provided as a template and should be used with caution.
"""

import time
import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import pandas as pd
import yaml
import logging
logger = logging.getLogger(__name__)
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import undetected_chromedriver as uc


class LinkedInEnricher:
    def __init__(self, config_path: str = "config/settings.yaml"):
        """Initialize LinkedIn enricher."""
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.linkedin_config = self.config['linkedin']
        self.driver = None

    def initialize_browser(self):
        """Initialize undetected Chrome browser."""
        logger.info("Initializing browser...")

        options = uc.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        # options.add_argument('--headless')  # Uncomment for headless mode

        self.driver = uc.Chrome(options=options)
        logger.info("Browser initialized")

    def close_browser(self):
        """Close browser session."""
        if self.driver:
            self.driver.quit()
            logger.info("Browser closed")

    def login_to_linkedin(self, username: str, password: str) -> bool:
        """
        Login to LinkedIn.

        SECURITY WARNING: Store credentials securely, not in code!
        Use environment variables or secure credential management.
        """
        try:
            logger.info("Attempting to login to LinkedIn...")

            self.driver.get("https://www.linkedin.com/login")
            time.sleep(3)

            # Enter username
            username_field = self.driver.find_element(By.ID, "username")
            username_field.send_keys(username)

            # Enter password
            password_field = self.driver.find_element(By.ID, "password")
            password_field.send_keys(password)

            # Click login button
            login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_button.click()

            time.sleep(5)

            # Check if login successful
            if "feed" in self.driver.current_url or "mynetwork" in self.driver.current_url:
                logger.info("Login successful!")
                return True
            else:
                logger.warning("Login may have failed - check manually")
                return False

        except Exception as e:
            logger.error(f"Login error: {e}")
            return False

    def search_profile_by_name_company(self, name: str, company: str = None) -> Optional[str]:
        """
        Search for LinkedIn profile by name and optionally company.

        Returns: LinkedIn profile URL if found, None otherwise
        """
        try:
            # Build search query
            if company:
                query = f"{name} {company}"
            else:
                query = name

            search_url = f"https://www.linkedin.com/search/results/people/?keywords={query.replace(' ', '%20')}"

            logger.info(f"Searching for: {query}")
            self.driver.get(search_url)

            time.sleep(3)

            # Wait for results
            wait = WebDriverWait(self.driver, 10)
            results = wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".reusable-search__result-container"))
            )

            if not results:
                logger.warning(f"No results found for {name}")
                return None

            # Get first result
            first_result = results[0]

            # Extract profile URL
            profile_link = first_result.find_element(By.CSS_SELECTOR, "a.app-aware-link")
            profile_url = profile_link.get_attribute("href")

            # Clean URL (remove query parameters)
            profile_url = profile_url.split('?')[0]

            logger.info(f"Found profile: {profile_url}")

            # Add delay to avoid rate limiting
            time.sleep(self.linkedin_config['scraping']['rate_limit_seconds'])

            return profile_url

        except TimeoutException:
            logger.warning(f"Timeout searching for {name}")
            return None
        except Exception as e:
            logger.error(f"Error searching for {name}: {e}")
            return None

    def scrape_profile_data(self, profile_url: str) -> Dict:
        """
        Scrape data from a LinkedIn profile.

        Returns dict with:
        - current_company
        - current_title
        - location
        - past_companies (list)
        """
        try:
            logger.info(f"Scraping profile: {profile_url}")

            self.driver.get(profile_url)
            time.sleep(3)

            profile_data = {
                'profile_url': profile_url,
                'current_company': None,
                'current_title': None,
                'location': None,
                'past_companies': []
            }

            # Scrape current position
            try:
                # Look for experience section
                exp_section = self.driver.find_element(By.ID, "experience")

                # Get first position (most recent)
                positions = self.driver.find_elements(By.CSS_SELECTOR, "#experience ~ * li")

                if positions:
                    first_position = positions[0]

                    # Extract current title
                    try:
                        title_elem = first_position.find_element(By.CSS_SELECTOR, ".t-bold span[aria-hidden='true']")
                        profile_data['current_title'] = title_elem.text
                    except:
                        pass

                    # Extract current company
                    try:
                        company_elem = first_position.find_element(By.CSS_SELECTOR, ".t-normal span[aria-hidden='true']")
                        profile_data['current_company'] = company_elem.text
                    except:
                        pass

            except Exception as e:
                logger.warning(f"Could not extract current position: {e}")

            # Scrape location
            try:
                location_elem = self.driver.find_element(By.CSS_SELECTOR, ".text-body-small.inline.t-black--light")
                profile_data['location'] = location_elem.text
            except:
                pass

            # Scrape past companies (last 3 years)
            try:
                all_positions = self.driver.find_elements(By.CSS_SELECTOR, "#experience ~ * li")

                for position in all_positions[1:]:  # Skip first (current)
                    try:
                        company_elem = position.find_element(By.CSS_SELECTOR, ".t-normal span[aria-hidden='true']")
                        company_name = company_elem.text

                        if company_name and company_name not in profile_data['past_companies']:
                            profile_data['past_companies'].append(company_name)

                        if len(profile_data['past_companies']) >= 3:
                            break
                    except:
                        continue

            except Exception as e:
                logger.warning(f"Could not extract past companies: {e}")

            # Add delay
            time.sleep(self.linkedin_config['scraping']['rate_limit_seconds'])

            return profile_data

        except Exception as e:
            logger.error(f"Error scraping profile {profile_url}: {e}")
            return {}

    def enrich_spoc_list(self, spocs_df: pd.DataFrame) -> pd.DataFrame:
        """
        Enrich a DataFrame of SPOCs with LinkedIn data.

        Expected columns: full_name, email, company_name, linkedin_url (optional)

        Returns enriched DataFrame with:
        - linkedin_url (updated if found)
        - current_company
        - current_title
        - location
        - past_companies
        - job_change_detected (boolean)
        """
        logger.info(f"Enriching {len(spocs_df)} SPOCs with LinkedIn data...")

        enriched_data = []

        for idx, row in spocs_df.iterrows():
            name = row.get('full_name', '')
            email = row.get('email', '')
            original_company = row.get('company_name', '')
            existing_linkedin = row.get('linkedin_url', '')

            logger.info(f"Processing {idx + 1}/{len(spocs_df)}: {name}")

            profile_data = {
                'email': email,
                'full_name': name,
                'original_company': original_company,
                'linkedin_url': existing_linkedin,
                'current_company': None,
                'current_title': None,
                'location': None,
                'past_companies': None,
                'job_change_detected': False,
                'enrichment_status': 'pending'
            }

            try:
                # If no LinkedIn URL, search for it
                if not existing_linkedin or pd.isna(existing_linkedin):
                    profile_url = self.search_profile_by_name_company(name, original_company)

                    if not profile_url:
                        profile_data['enrichment_status'] = 'not_found'
                        enriched_data.append(profile_data)
                        continue

                    profile_data['linkedin_url'] = profile_url
                else:
                    profile_url = existing_linkedin

                # Scrape profile data
                scraped_data = self.scrape_profile_data(profile_url)

                if scraped_data:
                    profile_data.update(scraped_data)
                    profile_data['past_companies'] = ', '.join(scraped_data.get('past_companies', []))

                    # Detect job change
                    current_company = scraped_data.get('current_company', '')
                    if current_company and original_company:
                        # Simple check - could be made more sophisticated
                        if current_company.lower() != original_company.lower():
                            profile_data['job_change_detected'] = True
                            logger.info(f"JOB CHANGE DETECTED: {name} moved from {original_company} to {current_company}")

                    profile_data['enrichment_status'] = 'success'
                else:
                    profile_data['enrichment_status'] = 'failed'

            except Exception as e:
                logger.error(f"Error enriching {name}: {e}")
                profile_data['enrichment_status'] = 'error'

            enriched_data.append(profile_data)

            # Save intermediate results every 10 records
            if (idx + 1) % 10 == 0:
                self._save_checkpoint(enriched_data, idx + 1)

        enriched_df = pd.DataFrame(enriched_data)

        logger.info(f"Enrichment complete: {len(enriched_df)} records processed")
        logger.info(f"Job changes detected: {enriched_df['job_change_detected'].sum()}")

        return enriched_df

    def _save_checkpoint(self, data: List[Dict], count: int):
        """Save intermediate results as checkpoint."""
        checkpoint_path = Path("data/enriched") / f"linkedin_checkpoint_{count}.csv"
        checkpoint_path.parent.mkdir(parents=True, exist_ok=True)

        df = pd.DataFrame(data)
        df.to_csv(checkpoint_path, index=False)

        logger.info(f"Checkpoint saved: {checkpoint_path}")

    def identify_job_change_opportunities(self, enriched_df: pd.DataFrame) -> pd.DataFrame:
        """
        Identify referral opportunities from job changes.

        Strategy types:
        1. SPOC moved to new company -> reach out at new company
        2. SPOC moved from company -> ask for referral back to old company
        """
        logger.info("Identifying job change opportunities...")

        # Filter for detected job changes
        job_changes = enriched_df[enriched_df['job_change_detected'] == True].copy()

        opportunities = []

        for _, row in job_changes.iterrows():
            # Strategy 1: Reach out at new company
            opportunities.append({
                'strategy': 'spoc_at_new_company',
                'spoc_name': row['full_name'],
                'spoc_email': row['email'],
                'spoc_linkedin': row['linkedin_url'],
                'spoc_current_company': row['current_company'],
                'spoc_current_title': row['current_title'],
                'original_company': row['original_company'],
                'past_companies': row['past_companies'],
                'priority': 'HIGH',
                'outreach_angle': f"We worked together when you were at {row['original_company']}, would love to work with you at {row['current_company']}"
            })

            # Strategy 2: Ask for referral to old company
            if row['original_company']:
                opportunities.append({
                    'strategy': 'reverse_referral_to_old_company',
                    'spoc_name': row['full_name'],
                    'spoc_email': row['email'],
                    'spoc_linkedin': row['linkedin_url'],
                    'spoc_current_company': row['current_company'],
                    'spoc_current_title': row['current_title'],
                    'referral_target_company': row['original_company'],
                    'priority': 'MEDIUM',
                    'outreach_angle': f"Since you've moved to {row['current_company']}, could you refer us to your contacts at {row['original_company']}?"
                })

        return pd.DataFrame(opportunities)


def main():
    """
    Main execution function.

    IMPORTANT: This script requires manual intervention for:
    1. LinkedIn login credentials (use environment variables)
    2. Handling CAPTCHAs
    3. Monitoring for rate limits
    """
    import os

    # Get credentials from environment variables
    linkedin_username = os.getenv('LINKEDIN_USERNAME')
    linkedin_password = os.getenv('LINKEDIN_PASSWORD')

    if not linkedin_username or not linkedin_password:
        logger.error("LinkedIn credentials not found in environment variables!")
        logger.info("Set LINKEDIN_USERNAME and LINKEDIN_PASSWORD before running")
        return

    enricher = LinkedInEnricher()

    try:
        # Initialize browser
        enricher.initialize_browser()

        # Login
        if not enricher.login_to_linkedin(linkedin_username, linkedin_password):
            logger.error("Login failed, aborting...")
            return

        # Load SPOCs to enrich
        spocs_df = pd.read_csv("data/processed/processed_spocs.csv")

        # Enrich SPOCs
        enriched_df = enricher.enrich_spoc_list(spocs_df)

        # Save enriched data
        output_path = Path("data/enriched")
        output_path.mkdir(parents=True, exist_ok=True)

        enriched_df.to_csv(output_path / "linkedin_enriched_spocs.csv", index=False)
        logger.info(f"Saved enriched data to {output_path / 'linkedin_enriched_spocs.csv'}")

        # Identify job change opportunities
        job_change_opps = enricher.identify_job_change_opportunities(enriched_df)

        if not job_change_opps.empty:
            job_change_opps.to_csv(output_path / "job_change_opportunities.csv", index=False)
            logger.info(f"Identified {len(job_change_opps)} job change opportunities")

    finally:
        # Always close browser
        enricher.close_browser()


if __name__ == "__main__":
    main()

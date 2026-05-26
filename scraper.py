"""
JobLens — Web Scraper Module
==============================
Scrapes job postings from Naukri.com and Indeed India using
BeautifulSoup and Selenium.

WHY TWO APPROACHES:
- BeautifulSoup: Fast, lightweight, works for static pages
- Selenium: Required for JavaScript-rendered content (Naukri uses React)

IMPORTANT: Live scraping may be blocked by anti-bot measures.
If scraping fails, the system falls back to the dummy data generator.
This ensures the platform always has data to work with.
"""

import os
import sys
import time
import sqlite3
import csv
import logging
from datetime import datetime

# Set up logging for scraper operations
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('JobLensScraper')

try:
    import requests
    from bs4 import BeautifulSoup
    BEAUTIFULSOUP_AVAILABLE = True
except ImportError:
    BEAUTIFULSOUP_AVAILABLE = False
    logger.warning("BeautifulSoup not installed. Install with: pip install beautifulsoup4 requests")

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    logger.warning("Selenium not installed. Install with: pip install selenium")

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data.master_skills import extract_skills_from_text


class NaukriScraper:
    """
    Scrapes job postings from Naukri.com using Selenium.
    
    Naukri uses JavaScript rendering, so we need Selenium to
    load the page fully before extracting content.
    
    Attributes:
        base_url (str): Base URL for Naukri job search
        driver: Selenium WebDriver instance
    """
    
    def __init__(self):
        """Initialize the scraper with headless Chrome configuration."""
        self.base_url = "https://www.naukri.com"
        self.driver = None
    
    def setup_driver(self):
        """
        Set up headless Chrome WebDriver.
        
        Headless mode runs Chrome without a visible window,
        which is faster and works on servers without displays.
        """
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")  # No visible browser window
            chrome_options.add_argument("--no-sandbox")  # Required for Linux servers
            chrome_options.add_argument("--disable-dev-shm-usage")  # Prevent crashes
            chrome_options.add_argument("--disable-gpu")  # Reduce resource usage
            chrome_options.add_argument(
                "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_page_load_timeout(30)
            logger.info("Chrome WebDriver initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            return False
    
    def scrape_jobs(self, keyword="data scientist", location="india", num_pages=5):
        """
        Scrape job postings from Naukri.com for a given keyword.
        
        Args:
            keyword (str): Job search keyword
            location (str): Location filter
            num_pages (int): Number of search result pages to scrape
            
        Returns:
            list: List of job posting dictionaries
        """
        if not self.setup_driver():
            logger.error("Cannot scrape: WebDriver setup failed")
            return []
        
        jobs = []
        keyword_url = keyword.replace(" ", "-")
        
        try:
            for page in range(1, num_pages + 1):
                url = f"{self.base_url}/{keyword_url}-jobs-in-{location}?k={keyword}&l={location}&experience=&nignbevent_src=jobsearchDeskGNB&page={page}"
                
                logger.info(f"Scraping page {page}: {url}")
                self.driver.get(url)
                
                # Wait for job cards to load
                time.sleep(3)
                
                try:
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "srp-jobtuple-wrapper"))
                    )
                except Exception:
                    logger.warning(f"Timeout waiting for job cards on page {page}")
                    continue
                
                # Parse the page
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                job_cards = soup.find_all('article', class_='jobTuple')
                
                if not job_cards:
                    # Try alternate selectors (Naukri changes their HTML frequently)
                    job_cards = soup.find_all('div', class_='srp-jobtuple-wrapper')
                
                for card in job_cards:
                    try:
                        job = self._parse_naukri_card(card)
                        if job:
                            jobs.append(job)
                    except Exception as e:
                        logger.warning(f"Error parsing job card: {e}")
                        continue
                
                logger.info(f"Page {page}: Found {len(job_cards)} jobs")
                time.sleep(2)  # Be respectful — don't hammer the server
                
        except Exception as e:
            logger.error(f"Scraping error: {e}")
        finally:
            if self.driver:
                self.driver.quit()
        
        return jobs
    
    def _parse_naukri_card(self, card):
        """
        Extract job details from a single Naukri job card HTML element.
        
        Args:
            card: BeautifulSoup element for a job card
            
        Returns:
            dict: Job posting data or None if parsing fails
        """
        try:
            # Extract job title
            title_elem = card.find('a', class_='title')
            job_title = title_elem.text.strip() if title_elem else None
            
            # Extract company name
            company_elem = card.find('a', class_='subTitle')
            company = company_elem.text.strip() if company_elem else "Unknown"
            
            # Extract location
            location_elem = card.find('li', class_='location')
            location = location_elem.text.strip() if location_elem else "India"
            
            # Extract salary
            salary_elem = card.find('li', class_='salary')
            salary = salary_elem.text.strip() if salary_elem else "Not Disclosed"
            
            # Extract experience
            exp_elem = card.find('li', class_='experience')
            experience = exp_elem.text.strip() if exp_elem else "Not Specified"
            
            # Extract job description snippet
            desc_elem = card.find('div', class_='job-description')
            description = desc_elem.text.strip() if desc_elem else ""
            
            # Extract skills from description
            skills = extract_skills_from_text(description + " " + (job_title or ""))
            
            if not job_title:
                return None
            
            return {
                "job_title": job_title,
                "company_name": company,
                "location": location.split(",")[0].strip(),
                "salary_range": salary,
                "salary_min": None,
                "salary_max": None,
                "required_skills": ", ".join(skills),
                "experience_required": experience,
                "experience_min": None,
                "experience_max": None,
                "job_description": description,
                "date_posted": datetime.now().strftime("%Y-%m-%d"),
                "portal_name": "Naukri.com",
                "company_tier": "mid"
            }
        except Exception as e:
            logger.warning(f"Error parsing Naukri card: {e}")
            return None


class IndeedScraper:
    """
    Scrapes job postings from Indeed India using BeautifulSoup.
    
    Indeed's search results are mostly server-rendered HTML,
    so BeautifulSoup works well without needing Selenium.
    
    Attributes:
        base_url (str): Base URL for Indeed India
        headers (dict): HTTP headers to mimic a real browser
    """
    
    def __init__(self):
        """Initialize with browser-mimicking headers to avoid blocks."""
        self.base_url = "https://in.indeed.com"
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9",
            "Accept-Language": "en-US,en;q=0.9",
        }
    
    def scrape_jobs(self, keyword="data scientist", location="India", num_pages=5):
        """
        Scrape job postings from Indeed India.
        
        Args:
            keyword (str): Search keyword
            location (str): Location filter
            num_pages (int): Number of pages to scrape (10 results per page)
            
        Returns:
            list: List of job posting dictionaries
        """
        if not BEAUTIFULSOUP_AVAILABLE:
            logger.error("BeautifulSoup is not available")
            return []
        
        jobs = []
        
        for page in range(num_pages):
            start = page * 10  # Indeed uses offset-based pagination
            url = f"{self.base_url}/jobs?q={keyword}&l={location}&start={start}"
            
            try:
                logger.info(f"Scraping Indeed page {page + 1}: {url}")
                response = requests.get(url, headers=self.headers, timeout=15)
                
                if response.status_code != 200:
                    logger.warning(f"HTTP {response.status_code} for {url}")
                    continue
                
                soup = BeautifulSoup(response.text, 'html.parser')
                job_cards = soup.find_all('div', class_='job_seen_beacon')
                
                for card in job_cards:
                    try:
                        job = self._parse_indeed_card(card)
                        if job:
                            jobs.append(job)
                    except Exception as e:
                        logger.warning(f"Error parsing Indeed card: {e}")
                        continue
                
                logger.info(f"Indeed page {page + 1}: Found {len(job_cards)} jobs")
                time.sleep(2)  # Rate limiting — be respectful
                
            except requests.RequestException as e:
                logger.error(f"Request failed for {url}: {e}")
                continue
        
        return jobs
    
    def _parse_indeed_card(self, card):
        """
        Extract job details from a single Indeed job card.
        
        Args:
            card: BeautifulSoup element for a job card
            
        Returns:
            dict: Job posting data or None if parsing fails
        """
        try:
            # Job title
            title_elem = card.find('h2', class_='jobTitle')
            job_title = title_elem.get_text(strip=True) if title_elem else None
            
            # Company
            company_elem = card.find('span', {'data-testid': 'company-name'})
            company = company_elem.get_text(strip=True) if company_elem else "Unknown"
            
            # Location
            location_elem = card.find('div', {'data-testid': 'text-location'})
            location = location_elem.get_text(strip=True) if location_elem else "India"
            
            # Salary
            salary_elem = card.find('div', class_='salary-snippet-container')
            salary = salary_elem.get_text(strip=True) if salary_elem else "Not Disclosed"
            
            # Description snippet
            desc_elem = card.find('div', class_='job-snippet')
            description = desc_elem.get_text(strip=True) if desc_elem else ""
            
            # Extract skills
            skills = extract_skills_from_text(description + " " + (job_title or ""))
            
            if not job_title:
                return None
            
            return {
                "job_title": job_title,
                "company_name": company,
                "location": location.split(",")[0].strip(),
                "salary_range": salary,
                "salary_min": None,
                "salary_max": None,
                "required_skills": ", ".join(skills),
                "experience_required": "Not Specified",
                "experience_min": None,
                "experience_max": None,
                "job_description": description,
                "date_posted": datetime.now().strftime("%Y-%m-%d"),
                "portal_name": "Indeed India",
                "company_tier": "mid"
            }
        except Exception as e:
            logger.warning(f"Error parsing Indeed card: {e}")
            return None


def save_scraped_jobs(jobs, db_path="data/jobs.db"):
    """
    Save scraped jobs to the SQLite database.
    
    Appends to existing data rather than replacing,
    so scraped data complements the generated data.
    
    Args:
        jobs (list): List of job dictionaries to save
        db_path (str): Path to the SQLite database
    """
    if not jobs:
        logger.info("No jobs to save")
        return
    
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Ensure table exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS job_postings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_title TEXT NOT NULL,
            company_name TEXT NOT NULL,
            location TEXT,
            salary_range TEXT,
            salary_min REAL,
            salary_max REAL,
            required_skills TEXT,
            experience_required TEXT,
            experience_min INTEGER,
            experience_max INTEGER,
            job_description TEXT,
            date_posted TEXT,
            portal_name TEXT,
            company_tier TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    inserted = 0
    for job in jobs:
        try:
            cursor.execute("""
                INSERT INTO job_postings 
                (job_title, company_name, location, salary_range, salary_min, salary_max,
                 required_skills, experience_required, experience_min, experience_max,
                 job_description, date_posted, portal_name, company_tier)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job["job_title"], job["company_name"], job["location"],
                job["salary_range"], job.get("salary_min"), job.get("salary_max"),
                job["required_skills"], job["experience_required"],
                job.get("experience_min"), job.get("experience_max"),
                job["job_description"], job["date_posted"],
                job["portal_name"], job.get("company_tier", "mid")
            ))
            inserted += 1
        except Exception as e:
            logger.warning(f"Error inserting job: {e}")
    
    conn.commit()
    conn.close()
    logger.info(f"Saved {inserted} scraped jobs to database")


def run_scraper():
    """
    Main scraping function that tries both Naukri and Indeed.
    
    Attempts to scrape from both portals. If scraping fails
    (which is common due to anti-bot measures), logs the error
    and returns whatever was collected.
    
    Returns:
        list: All scraped job postings
    """
    all_jobs = []
    
    # Search keywords for different data science roles
    keywords = [
        "data scientist", "data analyst", "machine learning engineer",
        "business analyst", "python developer"
    ]
    
    print("=" * 60)
    print("JobLens — Web Scraper")
    print("=" * 60)
    
    # Try Naukri.com with Selenium
    if SELENIUM_AVAILABLE:
        print("\n📡 Attempting to scrape Naukri.com...")
        naukri = NaukriScraper()
        for keyword in keywords:
            try:
                jobs = naukri.scrape_jobs(keyword=keyword, num_pages=2)
                all_jobs.extend(jobs)
                print(f"  ✓ '{keyword}': Found {len(jobs)} jobs")
            except Exception as e:
                print(f"  ✗ '{keyword}': Failed - {e}")
    else:
        print("\n⚠ Selenium not available — skipping Naukri.com")
    
    # Try Indeed India with BeautifulSoup
    if BEAUTIFULSOUP_AVAILABLE:
        print("\n📡 Attempting to scrape Indeed India...")
        indeed = IndeedScraper()
        for keyword in keywords:
            try:
                jobs = indeed.scrape_jobs(keyword=keyword, num_pages=2)
                all_jobs.extend(jobs)
                print(f"  ✓ '{keyword}': Found {len(jobs)} jobs")
            except Exception as e:
                print(f"  ✗ '{keyword}': Failed - {e}")
    else:
        print("\n⚠ BeautifulSoup not available — skipping Indeed")
    
    # Save results
    if all_jobs:
        save_scraped_jobs(all_jobs)
        print(f"\n✓ Total scraped: {len(all_jobs)} jobs")
    else:
        print("\n⚠ No jobs scraped. This is normal if sites are blocking requests.")
        print("  The platform will use generated dummy data instead.")
    
    return all_jobs


if __name__ == "__main__":
    run_scraper()

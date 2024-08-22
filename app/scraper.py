import os
import re
import time
import logging
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from concurrent.futures import ThreadPoolExecutor
import google.generativeai as genai

from db import collection
from constants import MAIL, PASSWORD

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)

class AlumniProfile:
    def __init__(self, name, bio, location, contact_url, contact, jobs, institutes):
        self.name = name
        self.bio = bio
        self.location = location
        self.contact_url = contact_url
        self.contact = contact
        self.jobs = jobs
        self.institutes = institutes

    def to_dict(self):
        return {
            'name': self.name,
            'bio': self.bio,
            'location': self.location,
            'contact_url': self.contact_url,
            'contact': self.contact,
            'jobs': [
                {
                    'title': job[0] if len(job) > 0 else "Unknown",
                    'company': job[1] if len(job) > 1 else "Unknown",
                    'start_date': job[2] if len(job) > 2 else "Unknown",
                    'end_date': job[3] if len(job) > 3 else "Unknown",
                    'duration': job[4] if len(job) > 4 else "Unknown"
                }
                for job in self.jobs
            ],
            'institutes': [
                {
                    'name': institute[0] if len(institute) > 0 else "Unknown",
                    'degree': institute[1] if len(institute) > 1 else "Unknown",
                    'start_year': institute[2] if len(institute) > 2 else "Unknown",
                    'end_year': institute[3] if len(institute) > 3 else "Unknown"
                }
                for institute in self.institutes
            ]
        }


class LinkedInScrapper:
    def __init__(self, email, password):
        self.driver = webdriver.Chrome()
        self.email = email
        self.password = password
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("Google API key not found. Please set the GOOGLE_API_KEY environment variable.")
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel("gemini-pro")

    def get_gemini_response(self, bio):
        try:
            response = self.model.generate_content(bio)
            return response.text
        except Exception as e:
            logging.error(f"Error fetching Gemini response: {e}")
            return bio

    def login(self, timeout=10):
        try:
            self.driver.get('https://www.linkedin.com/login')
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, 'username')))

            email_elem = self.driver.find_element(By.ID, 'username')
            email_elem.send_keys(self.email)

            password_elem = self.driver.find_element(By.ID, 'password')
            password_elem.send_keys(self.password)

            password_elem.submit()

            if self.driver.current_url.startswith('https://www.linkedin.com/checkpoint/challenge/'):
                verification_code_input = self.driver.find_element(By.ID, 'input__email_verification_pin')
                verification_code = input('Please enter the 2-step verification code: ')
                verification_code_input.send_keys(verification_code)
                verification_code_input.submit()

            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'global-nav__primary-link')))
            logging.info("Login successful")
        except Exception as e:
            logging.error(f"Error during login: {e}")
            raise

    def scroll(self):
        SCROLL_PAUSE_TIME = 2
        final_scroll = self.driver.execute_script('return document.body.scrollHeight')
        initial_scroll = 0
        self.driver.execute_script(f'window.scrollTo({initial_scroll}, {final_scroll});')
        time.sleep(SCROLL_PAUSE_TIME)

    def fetch_and_save_profiles(self):
        connection_links = set()
        try:
            self.driver.get('https://www.linkedin.com/mynetwork/invite-connect/connections/')
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'mn-connections')))
            
            while True:
                self.scroll()
                time.sleep(2)  # Wait for the content to load
                
                page = self.driver.page_source
                soup = BeautifulSoup(page, 'html.parser')

                # Extract profile links
                links = set()
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    if '/in/' in href:
                        links.add(f"https://www.linkedin.com{href}")

                # Process and save each profile
                for profile_url in links:
                    try:
                        profile = self.scrape(profile_url)
                        self.save_to_mongo(profile)
                    except Exception as e:
                        logging.error(f"Error processing profile {profile_url}: {e}")

                # Click "Load more" if it exists
                try:
                    load_more_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Show more')]")
                    if load_more_button:
                        load_more_button.click()
                        time.sleep(3)  # Wait for new profiles to load
                    else:
                        break
                except Exception as e:
                    logging.info("No more connections to load or error occurred.")
                    break

        except Exception as e:
            logging.error(f"Error fetching connection links: {e}")

        logging.info(f"Total profiles processed: {len(connection_links)}")


    def basic_info(self, profile):
        try:
            self.driver.get(profile)
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'mt2')))
            page = self.driver.page_source
            basic = BeautifulSoup(page, 'html.parser').find('div', {'class': 'mt2 relative'})

            name_elem = basic.find('h1')
            name = name_elem.get_text().strip() if name_elem else "Name not found"

            bio_elem = basic.find('div', {'class': 'text-body-medium break-words'})
            bio = bio_elem.get_text().strip() if bio_elem else "Bio not found"

            location_elem = basic.find_all('span', {'class': 'text-body-small inline t-black--light break-words'})
            location = location_elem[0].get_text().strip() if location_elem else "Location not found"

            contact_elem = basic.find('a', {'id': 'top-card-text-details-contact-info'})
            contact = contact_elem.get("href") if contact_elem else None
            contact_url = f"https://www.linkedin.com{contact}" if contact else None

            return name, bio, location, contact_url
        except Exception as e:
            logging.error(f"Error fetching basic info: {e}")
            return "Unknown", "Unknown", "Unknown", None

    def contact(self, contact_url):
        contacts = {
            "email": None,
            "phone_number": None,
            "other": []
        }
        
        if not contact_url:
            logging.warning("No contact URL found.")
            return contacts
        
        try:
            self.driver.get(contact_url)
            self.scroll()  # Ensure the page is fully loaded
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'pv-contact-info__contact-type')))
            
            page = self.driver.page_source
            soup = BeautifulSoup(page, 'html.parser')
            
            # Log the entire HTML for the contact section for debugging purposes
            logging.info(f"Contact page HTML: {soup.prettify()}")

            # Attempt to fetch email and phone number
            contact_sections = soup.find_all('section', {'class': 'pv-contact-info__contact-type'})
            
            for section in contact_sections:
                contact_type = section.find('h3', {'class': 'pv-contact-info__header'})
                if contact_type:
                    label = contact_type.get_text().strip().lower()
                    contact_info = section.find_all('a', href=True)
                    
                    if label == 'email':
                        for link in contact_info:
                            if 'mailto:' in link['href']:
                                contacts['email'] = link['href'].replace('mailto:', '').strip()
                                logging.info(f"Found email: {contacts['email']}")
                    
                    elif label == 'phone':
                        phone_info = section.find('span', {'class': 't-14 t-black t-normal'})
                        if phone_info:
                            contacts['phone_number'] = phone_info.get_text().strip()
                            logging.info(f"Found phone number: {contacts['phone_number']}")
                    
                    else:
                        # Log and save other contact information
                        for link in contact_info:
                            contacts['other'].append({
                                'label': label,
                                'url': link['href']
                            })
                        logging.info(f"Found other contact info: {contacts['other']}")
                        
        except Exception as e:
            logging.error(f"Error fetching contact info: {e}")
        
        if not contacts['email']:
            logging.warning("Email not found in the contact info.")
        if not contacts['phone_number']:
            logging.warning("Phone number not found in the contact info.")
        
        return contacts


    def experience(self, experience_url):
        jobs = []
        try:
            self.driver.get(experience_url)
            self.scroll()
            page = self.driver.page_source
            experiences = BeautifulSoup(page, 'html.parser').find_all("li", {"class": 'pvs-list__paged-list-item '
                                                                                      'artdeco-list__item '
                                                                                      'pvs-list__item--line-separated '
                                                                                      'pvs-list__item--one-column'})
            for experience in experiences:
                data = []
                title = experience.find('div', {'class': 'display-flex flex-wrap align-items-center full-height'})
                if title:
                    title2 = title.find('span', {'aria-hidden': 'true'}).get_text().strip()
                    data.append(title2)
                    company = experience.find('span', {'class': 't-14 t-normal'})
                    company2 = company.find('span', {'aria-hidden': 'true'}).get_text().strip()
                    data.append(company2)
                    duration = experience.find('span', {'class': 't-14 t-normal t-black--light'})
                    duration2 = duration.find('span', {'aria-hidden': 'true'}).get_text().strip('.')
                    duration2 = re.split(' - | · ', duration2)
                    data.extend(duration2)
                    jobs.append(data)
        except Exception as e:
            logging.error(f"Error fetching experience: {e}")
        return jobs

    def education(self, education_url):
        institutes = []
        try:
            self.driver.get(education_url)
            self.scroll()
            page = self.driver.page_source
            educations = BeautifulSoup(page, 'html.parser').find('div', {'class': 'scaffold-finite-scroll__content'})
            if educations:
                educations = educations.find_all('a', {
                    'class': 'optional-action-target-wrapper display-flex flex-column '
                             'full-width'})
                for education in educations:
                    inst = []
                    institute = education.find_all('span', {'aria-hidden': 'true'})
                    for span in institute:
                        spans = span.text.split(' - ')
                        inst.extend(spans)
                    institutes.append(inst)
            else:
                logging.error("No education section found")
        except Exception as e:
            logging.error(f"Error fetching education: {e}")
        return institutes

    def scrape(self, profile_url):
        name, bio, location, contact_url = self.basic_info(profile_url)

        # Update bio using Gemini API
        updated_bio = self.get_gemini_response(bio)
        contact = self.contact(contact_url)
        experience_url = profile_url + 'details/experience/'
        jobs = self.experience(experience_url)
        education_url = profile_url + 'details/education'
        institutes = self.education(education_url)

        # Create the AlumniProfile object
        profile = AlumniProfile(name, updated_bio, location, contact_url, contact, jobs, institutes)
    
        return profile

    def save_to_mongo(self, profile):
        try:
            profile_dict = profile.to_dict()
            collection.insert_one(profile_dict)
            logging.info("Profile saved to MongoDB")
        except Exception as e:
            logging.error(f"Error saving profile to MongoDB: {e}")

    def quit(self):
        self.driver.quit()

def scrape_profiles(links):
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(scraper.scrape, links))
    return results

if __name__ == "__main__":
    mail = MAIL
    key = PASSWORD
    scraper = LinkedInScrapper(mail, key)
    scraper.login()
    scraper.fetch_and_save_profiles()
    scraper.quit()


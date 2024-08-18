import os
import re
import time
import json
import logging
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import google.generativeai as genai

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
                    'title': job[0],
                    'company': job[1],
                    'start_date': job[2],
                    'end_date': job[3],
                    'duration': job[4]
                }
                for job in self.jobs
            ],
            'institutes': [
                {
                    'name': institute[0],
                    'degree': institute[1],
                    'start_year': institute[2],
                    'end_year': institute[3]
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
        contacts = []
        if not contact_url:
            return contacts

        try:
            self.driver.get(contact_url)
            self.scroll()
            page = self.driver.page_source
            info = BeautifulSoup(page, 'html.parser').find('div',
                                                           {'class': 'pv-profile-section__section-info section-info'})
            profile_elem = info.find_all('section', {'class': 'pv-contact-info__contact-type'})

            for profile in profile_elem[1:]:
                all_a_tags = profile.find_all('a')
                href_links = [tag.get('href') for tag in all_a_tags if tag.get('href')]
                contacts.append(href_links)
        except Exception as e:
            logging.error(f"Error fetching contact info: {e}")
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
    
    def quit(self):
        self.driver.quit()




def scrape_profiles(links):
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(scraper.scrape, links))
    return results


def export_to_json(profiles, directory='./Objects/'):
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    for i, profile in enumerate(profiles):
        file_path = os.path.join(directory, f'profile_{i + 1}.json')
        with open(file_path, 'w') as f:
            json.dump(profile.to_dict(), f, indent=4)
        logging.info(f"Exported profile {i + 1} to {file_path}")


if __name__ == "__main__":
    links = ["https://www.linkedin.com/in/prajwaldeep-kamble-850792225/"]

    mail = "chsuryasaketh@gmail.com"
    key = "Alumnnet"
    scraper = LinkedInScrapper(mail, key)
    scraper.login()
    profiles = scrape_profiles(links)
    
    # Export the profiles to JSON files
    export_to_json(profiles)
    
    for profile in profiles:
        print(profile.jobs)
        print(profile.institutes)
    
    scraper.quit()

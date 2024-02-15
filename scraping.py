import re
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait


class LinkedInScrapper:
    def __init__(self, email, password):
        self.driver = webdriver.Chrome()
        self.email = email
        self.password = password

    def login(self, timeout=10):
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

    def scroll(self):

        SCROLL_PAUSE_TIME = 2
        final_scroll = self.driver.execute_script('return document.body.scrollHeight')
        initial_scroll = 0
        self.driver.execute_script(f'window.scrollTo({initial_scroll}, {final_scroll});')
        time.sleep(SCROLL_PAUSE_TIME)

    def basic_info(self, profile):
        self.driver.get(profile)
        page = self.driver.page_source
        basic = BeautifulSoup(page, 'html.parser').find('div', {'class': 'mt2 relative'})
        name_elem = basic.find('h1')
        name = name_elem.get_text().strip()

        bio_elem = basic.find('div', {'class': 'text-body-medium break-words'})
        bio = bio_elem.get_text().strip()

        location_elem = basic.find_all('span', {'class': 'text-body-small inline t-black--light break-words'})
        location = location_elem[0].get_text().strip()

        contact_elem = basic.find('a', {'id': 'top-card-text-details-contact-info'})
        contact = contact_elem.get("href")
        contact_url = "https://www.linkedin.com" + contact
        return name, bio, location, contact_url

    def contact(self, contact_url):
        contacts = []
        self.driver.get(contact_url)
        self.scroll()
        page = self.driver.page_source
        info = BeautifulSoup(page, 'html.parser').find('div', {'class': 'pv-profile-section__section-info section-info'})
        profile_elem = info.find_all('section', {'class': 'pv-contact-info__contact-type'})

        for profile in profile_elem[1:]:
            all_a_tags = profile.find_all('a')
            href_links = [tag.get('href') for tag in all_a_tags if tag.get('href')]
            # h3_tag = profile.find('h3', class_='pv-contact-info__header t-16 t-black t-bold')
            # if h3_tag and h3_tag.text.strip() == 'Email':
            #     mail = href_links
            # if h3_tag and h3_tag.text.strip() == 'Phone':
            #     span_tag = profile.find('span', class_='t-14 t-black t-normal')
            #     if span_tag:
            #         phone = span_tag.text.strip()
            contacts.append(href_links)
        return contacts

    def experience(self, experience_url):
        jobs = []
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
        return jobs

    def education(self, education_url):
        institutes = []
        self.driver.get(education_url)
        self.scroll()
        page = self.driver.page_source
        educations = BeautifulSoup(page, 'html.parser').find_all('a', {
            'class': 'optional-action-target-wrapper display-flex flex-column '
                     'full-width'})
        for education in educations:
            inst = []
            institute = education.find_all('span', {'aria-hidden': 'true'})
            for span in institute:
                spans = span.text.split(' - ')
                inst.extend(spans)
            institutes.append(inst)
        return institutes

    def scrape(self, profile_url):

        name, bio, location, contact_url = self.basic_info(profile_url)

        contact = self.contact(contact_url)

        experience_url = profile_url + 'details/experience/'
        jobs = self.experience(experience_url)

        education_url = profile_url + 'details/education'
        institutes = self.education(education_url)

        # print(f"{name}\n{bio}\n{location}\n{contact_url}\n{contact}\n{jobs}\n{institutes}")
        return name, bio, location, contact_url, contact, jobs, institutes

    def quit(self):
        self.driver.quit()


# mail = "chsuryasaketh@gmail.com"
# key = "Alumnnet"
# scraper = LinkedInScrapper(mail, key)
# scraper.login()
# scraper.scrape("https://www.linkedin.com/in/kunalshah1/")
# scraper.quit()

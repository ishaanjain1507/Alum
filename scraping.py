import re
import time
import json
import os

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait


# Code defining the login function for the scraper
def login(driver_name, email_value, password_value, timeout=10):
    driver_name.get("https://www.linkedin.com/login")
    WebDriverWait(driver_name, 10).until(EC.presence_of_element_located((By.ID, "username")))

    email_elem = driver_name.find_element(By.ID, "username")
    email_elem.send_keys(email_value)

    password_elem = driver_name.find_element(By.ID, "password")
    password_elem.send_keys(password_value)
    password_elem.submit()

    if driver_name.current_url.startswith('https://www.linkedin.com/checkpoint/challenge/'):
        verification_code_input = driver_name.find_element(By.ID, "input__email_verification_pin")
        # Prompt the user to enter the verification code
        verification_code = input("Please enter the 2-step verification code: ")

        # Enter the verification code into the input field
        verification_code_input.send_keys(verification_code)
        verification_code_input.submit()  # Or use other appropriate actions to submit the code

    WebDriverWait(driver_name, timeout).until(
        EC.presence_of_element_located((By.CLASS_NAME, "global-nav__primary-link")))


def scroll(driver_name):
    time.sleep(5)

    start = time.time()

    # will be used in the while loop
    initial_value = 0
    final_scroll = 1000

    while True:
        driver_name.execute_script(f"window.scrollTo({initial_value}, {final_scroll});")
        # this command scrolls the window starting from
        # the pixel value stored in the initial_value
        # variable to the pixel value stored at the
        # final_scroll variable
        initial_value = final_scroll
        final_scroll += 1000

        # we will stop the script for 5 seconds so that
        # the data can load
        time.sleep(5)
        # You can change it as per your needs and internet speed

        end = time.time()

        # We will scroll for 15 seconds.
        # You can change it as per your needs and internet speed
        if round(end - start) > 15:
            break

try:
    os.system('mkdir ./Objects/')
    print("Folder \'Objects\' created")
except FileExistsError:
    print("Folder exists")

driver = webdriver.Chrome()

# Don't forget to enter your login credentials here
email = "chsuryasaketh@gmail.com"
password = "Alumnnet"
login(driver, email, password)

time.sleep(5)

# paste the URL of Kunal's profile here
# Url for testing
profile_url = "https://www.linkedin.com/in/kunalshah1/"

# this will open the link
driver.get(profile_url)

src = driver.page_source

# Now using beautiful soup
soup = BeautifulSoup(src, 'html.parser')

# Extracting the HTML of the complete introduction box
intro = soup.find('div', {'class': 'mt2 relative'})

name_loc = intro.find("h1")
name = name_loc.get_text().strip() if name_loc else "Name not found"

works_at_loc = intro.find("div", {'class': 'text-body-medium break-words'})
works_at = works_at_loc.get_text().strip() if works_at_loc else "Works at not found"

location_loc = intro.find_all("span", {'class': 'text-body-small inline t-black--light break-words'})
location = location_loc[0].get_text().strip() if location_loc else "Location not found"

a_tag = soup.find('a', {'id': 'top-card-text-details-contact-info'})
print(a_tag)
contact = a_tag.get("href") if a_tag else "Contact info not found"
contact_url = "https://www.linkedin.com"
contact_url += contact

print("Name -->", name,
      "\nWorks At -->", works_at,
      "\nLocation -->", location,
      "\nContact info -->", contact_url)

time.sleep(5)

driver.get(contact_url)

src2 = driver.page_source

# Now using beautiful soup
soup2 = BeautifulSoup(src2, 'html.parser')
info = soup2.find('div', {'class': 'pv-profile-section__section-info section-info'})
profile_loc = info.find_all("section", {'class': 'pv-contact-info__contact-type'})
# Not finding info about the profile link as already present
for loc in profile_loc[1:]:
    all_a_tags = loc.find_all('a')
    href_links = [tag.get('href') for tag in all_a_tags if tag.get('href')]
    h3_tag = loc.find('h3', class_='pv-contact-info__header t-16 t-black t-bold')
    if h3_tag and h3_tag.text.strip() == 'Email':
        email = href_links
        print(f"email: {email}\n")
    if h3_tag and h3_tag.text.strip() == 'Phone':
        span_tag = loc.find('span', class_='t-14 t-black t-normal')
        if span_tag:
            phone = span_tag.text.strip()
            print(f"Phone: {phone}\n")
    print(href_links)
experience_url = profile_url + "details/experience/"
# this will open the link
driver.get(experience_url)
scroll(driver)
src3 = driver.page_source

# Now using beautiful soup
soup3 = BeautifulSoup(src3, 'html.parser')
experience = soup3.find("div", {"class": "scaffold-finite-scroll__content"})
# print(experience)
jobs = []
experiences = experience.find_all("li", {
    "class": "pvs-list__paged-list-item artdeco-list__item pvs-list__item--line-separated pvs-list__item--one-column"})
for experienc in experiences:
    data = []
    title = experienc.find("div", {"class": "display-flex flex-wrap align-items-center full-height"})
    title2 = title.find("span", {"aria-hidden": "true"}).get_text().strip()
    #     print(title2)
    data.append(title2)
    company = experienc.find("span", {"class": "t-14 t-normal"})
    company2 = company.find("span", {"aria-hidden": "true"}).get_text().strip()
    data.append(company2)
    duration = experienc.find("span", {"class": "t-14 t-normal t-black--light"})
    duration2 = duration.find("span", {"aria-hidden": "true"}).get_text().strip('.')
    duration2 = re.split(' - | · ', duration2)
    data.extend(duration2)
    jobs.append(data)

obj = {
    "Name" : name,
    "Company" : works_at,
    "Location" : location,
    "Contact Info" : contact_url,
    "Jobs" : jobs
}

print(jobs)


with open('./Objects/' + name + ".json", 'w') as file:
    json.dump(obj, file)
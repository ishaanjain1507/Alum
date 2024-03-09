import psycopg2 as psy
import scraping as scrap
import app
import pandas as pd

data = pd.read_csv('alumni data - Form Responses 1.csv', na_values="", keep_default_na=False).astype(str)
data.fillna("", inplace=True)
data.replace("nan", "", inplace=True)
# for i,j in data.iterrows():
#     print(j["Name"])
mail = "chsuryasaketh@gmail.com"
key = "Alumnnet"
scraper = scrap.LinkedInScrapper(mail, key)
scraper.login()
# links = data['linked in profile url']
con = psy.connect(host="localhost", database="alumn", user="postgres", password="1656", port=5432)
cur = con.cursor()

cur.execute("""create table if not exists profile(
name varchar(255),
bio varchar(255),
location varchar(255),
contact varchar(255) primary key,
branch varchar(5),
year varchar(3),
programme varchar(5)
);""")

cur.execute("""create table if not exists personal_mails(
id varchar(255) REFERENCES profile(contact)
    ON DELETE CASCADE,
mail_id varchar(255)
);""")

cur.execute("""create table if not exists numbers(
id varchar(255) REFERENCES profile(contact)
    ON DELETE CASCADE,
phone varchar(10)
);""")

cur.execute("""create table if not exists jobs(
id varchar(255) REFERENCES profile(contact)
    ON DELETE CASCADE,
    post varchar(255),
    company varchar(255)
) """)

cur.execute("""create table if not exists education(
id varchar(255) REFERENCES profile(contact)
    ON DELETE CASCADE,
    college varchar(255),
    degree varchar(255)
) """)

for i, j in data.iterrows():
    name, bio, location, contact_url, contact, jobs_array, edu_array = scraper.scrape(j["linked in profile url"])
    bio = bio[:255]

    # bio = app.edit_bio(bio)
    roll = j["Email Address"].lower().split('@')[0]
    branch = roll[:2]
    year = roll[2:4]
    programme = roll[4:9]
    email = j["personal mail"]
    phone1 = j["phone number "]
    phone1 = phone1.replace(".0", "")
    print(phone1)
    cur.execute("""insert into profile values (%s, %s, %s, %s, %s, %s, %s)""",
                (name, bio, location, contact_url, branch, year, programme))
    if email != "":
        cur.execute("""insert into personal_mails values (%s, %s)""", (contact_url, email))
    if len(phone1) == 10:
        cur.execute("""insert into numbers values (%s, %s)""", (contact_url, phone1))
    for job in jobs_array:
        cur.execute("""insert into jobs values (%s, %s, %s)""",
                    (contact_url, job[0], job[1]))
    for edu in edu_array:
        cur.execute("""insert into education values (%s, %s, %s)""",
                    (contact_url, edu[0], edu[1]))

con.commit()
cur.close()
con.close()
scraper.quit()

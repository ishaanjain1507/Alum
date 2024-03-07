import psycopg2 as psy
import scraping as scrap
import app
import pandas as pd

# NAME,BlockingIOError = (LINK)
data = pd.read_csv('alumni data - Form Responses 1.csv')
data.fillna("", inplace = True)
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
branch varchar(255),
year varchar(255),
programme varchar(255)
);""")

cur.execute("""create table if not exists personal_mails(
id varchar(255) REFERENCES profile(contact)
    ON DELETE CASCADE,
mail_id varchar(255)
);""")

cur.execute("""create table if not exists numbers(
id varchar(255) REFERENCES profile(contact)
    ON DELETE CASCADE,
phone varchar(255)
);""")

# cur.execute("""create table if not exists jobs(
# id varchar(255) primary key REFERENCES profile(contact)
#     ON DELETE CASCADE,
# ) """)
for i,j in data.iterrows():
    name, bio, location, contact_url, contact, jobs, institutes = scraper.scrape(j["linked in profile url"])
    # bio = app.edit_bio(bio)
    roll = j["Roll number"].lower()
    branch = roll[:2]
    year = roll[2:4]
    programme = roll[4:9]
    email = j["personal mail"]
    phone1 = j["phone number "]
    print(phone1)
    phone2 = j["Alternative phone number"]
    cur.execute("""insert into profile values (%s, %s, %s, %s, %s, %s, %s)""", (name, bio, location, contact_url, branch, year, programme))
    if email != "":
        cur.execute("""insert into personal_mails values (%s, %s)""", (contact_url, email))
    if phone1 != "":
        cur.execute("""insert into numbers values (%s, %s)""", (contact_url, phone1))
    if phone2 != "":
        cur.execute("""insert into numbers values (%s, %s)""", (contact_url, phone2))
    # cur.execute("""select * from profile;""")
# for row in cur.fetchall():
#     print(row)

con.commit()
cur.close()
con.close()
scraper.quit()

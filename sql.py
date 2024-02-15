import psycopg2 as psy
import scraping as scrap

mail = "chsuryasaketh@gmail.com"
key = "Alumnnet"
scraper = scrap.LinkedInScrapper(mail, key)
scraper.login()
links = ["https://www.linkedin.com/in/kunalshah1/", "https://www.linkedin.com/in/balmykhol/",
         "https://www.linkedin.com/in/kunalshah/"]
con = psy.connect(host="localhost", database="alumn", user="postgres", password="1656", port=5432)
cur = con.cursor()

cur.execute("""create table if not exists alumn(
name varchar(255),
bio varchar(255),
location varchar(255),
contact varchar(255) primary key
);""")
# for link in links:
#     name, bio, location, contact_url, contact, jobs, institutes = scraper.scrape(link)
#     cur.execute("""insert into alumn values (%s, %s, %s, %s)""", (name, bio, location, contact_url))
cur.execute("""select * from alumn;""")
for row in cur.fetchall():
    print(row)

con.commit()
cur.close()
con.close()
scraper.quit()

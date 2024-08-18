import unittest
from app.scraper import LinkedInScrapper

class TestLinkedInScrapper(unittest.TestCase):
    def test_basic_info(self):
        scraper = LinkedInScrapper("https://www.linkedin.com/in/ishaan-jain-148775214/", "Sj@55888")
        scraper.driver = None  # Mock driver to avoid actual login
        name, bio, location, contact_url = scraper.basic_info("https://www.linkedin.com/in/prachi-jain-7a7b22a1/")
        self.assertIsInstance(name, str)
        self.assertIsInstance(bio, str)
        self.assertIsInstance(location, str)
        self.assertIsNone(contact_url)

    def test_gemini_response(self):
        scraper = LinkedInScrapper("test_email", "test_password")
        bio = "Test bio"
        updated_bio = scraper.get_gemini_response(bio)
        self.assertIsInstance(updated_bio, str)

if __name__ == "__main__":
    unittest.main()

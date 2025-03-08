import os
import time
import random
import pandas as pd
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Generate a random user agent
from fake_useragent import UserAgent
ua = UserAgent()

chrome_options = uc.ChromeOptions()
chrome_options.headless = False
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_argument(f"user-agent={ua.random}")

# Load credentials from environment variables
linkedin_username = os.getenv("LINKEDIN_USER")
linkedin_password = os.getenv("LINKEDIN_PASS")

if not linkedin_username or not linkedin_password:
    raise Exception("LinkedIn credentials not found. Set environment variables first.")


def slow_down():
    """Adds a random delay to mimic human behavior"""
    time.sleep(random.uniform(3, 8))


def login(driver):
    """Logs into LinkedIn"""
    driver.get("https://www.linkedin.com/login")
    time.sleep(random.uniform(3, 5))

    try:
        email_input = driver.find_element(By.ID, "username")
        password_input = driver.find_element(By.ID, "password")

        email_input.send_keys(linkedin_username)
        password_input.send_keys(linkedin_password)
        password_input.send_keys(Keys.RETURN)

        time.sleep(random.uniform(5, 7))  # Wait to ensure login success
    except NoSuchElementException:
        print("❌ Error: Login elements not found!")
        driver.quit()
        exit()


def get_company_url(driver, company_name):
    """Searches for the company's LinkedIn page and returns the URL"""
    search_url = f"https://www.linkedin.com/search/results/companies/?keywords={company_name.replace(' ', '%20')}"
    try:
        driver.get(search_url)
        time.sleep(random.uniform(3, 6))

        first_result = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//a[contains(@href, '/company/')]"))
        )
        return first_result.get_attribute("href")
    except TimeoutException:
        print(f"⏳ Timeout error while searching for {company_name}. Retrying...")
        return get_company_url(driver, company_name)
    except Exception as e:
        print(f"❌ Error fetching LinkedIn page for {company_name}: {e}")
        return None


def scrape_about_section(driver, company_url):
    """Scrapes the company's 'About' section from LinkedIn"""
    about_url = company_url + "about/"

    try:
        driver.get(about_url)
        time.sleep(random.uniform(3, 6))

        # Scroll down slowly to trigger dynamic loading
        for _ in range(3):
            driver.execute_script("window.scrollBy(0, 300);")
            time.sleep(random.uniform(2, 4))

    except TimeoutException:
        print(f"⏳ Timeout while loading {about_url}. Retrying once...")
        return scrape_about_section(driver, company_url)
    except Exception as e:
        print(f"❌ Error scraping {about_url}: {e}")
        return {}

    def safe_find(xpath, attribute=None):
        """Safely find elements and return text or 'N/A' if not found"""
        try:
            element = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, xpath)))
            return element.get_attribute(attribute) if attribute else element.text.strip()
        except:
            return "N/A"

    overview = safe_find("//h2[text()='Overview']/following-sibling::p")
    website = safe_find("//dt[h3[text()='Website']]/following-sibling::dd//a", "href")
    industry = safe_find("//dt[h3[text()='Industry']]/following-sibling::dd[contains(@class, 'text-body-medium')]")
    company_size = safe_find("//h3[text()='Company size']/following::dd[1]")
    headquarters = safe_find("//h3[text()='Headquarters']/following::dd[1]")
    founded = safe_find("//h3[text()='Founded']/following::dd[1]")
    specialties = safe_find("//h3[text()='Specialties']/following::dd[1]")

    if "linkedin.com" in website:
        website = "N/A"

    return {
        "Overview": overview,
        "Website": website,
        "Industry": industry,
        "Company Size": company_size,
        "Headquarters": headquarters,
        "Founded": founded,
        "Specialties": specialties
    }


def scrape_people_section(driver, company_url):
    """Scrapes 'Where they live' and 'What they do' from the People section"""
    people_url = company_url + "people/"

    try:
        driver.get(people_url)
        time.sleep(random.uniform(3, 6))

        # Scroll down to load more data
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(random.uniform(2, 4))

        # Expand 'Show More' button if it exists
        try:
            show_more_btn = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'Show more')]"))
            )
            show_more_btn.click()
            time.sleep(random.uniform(2, 4))
        except:
            pass  # No 'Show More' button, continue normally

    except Exception as e:
        print(f"❌ Error scraping {people_url}: {e}")
        return {"What_they_do": "N/A", "Where_they_live": "N/A"}

    def extract_data(section_title):
        """Extracts data from the 'What they do' or 'Where they live' section"""
        try:
            section = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, f"//h3[contains(text(), '{section_title}')]/following-sibling::ul"))
            )
            items = section.find_elements(By.TAG_NAME, "li")

            data_dict = {}
            for item in items:
                key = item.find_element(By.TAG_NAME, "span").text.strip()
                value = item.find_element(By.TAG_NAME, "strong").text.strip()
                data_dict[key] = value

            return data_dict
        except:
            return {}

    where_they_live = extract_data("Where they live")
    what_they_do = extract_data("What they do")

    return {
        "Where_they_live": str(where_they_live),  # Store as a string (dictionary format)
        "What_they_do": str(what_they_do)
    }


def process_companies(driver, data, output_file):
    """Reads company names from CSV, fetches data, and saves to CSV"""
    df = pd.read_csv(data)
    results = []

    for index, row in df.iterrows():
        company_name = row['Company_Name']
        print(f"🔍 Searching for {company_name} on LinkedIn...")

        company_url = get_company_url(driver, company_name)
        if company_url:
            about_data = scrape_about_section(driver, company_url)
            people_data = scrape_people_section(driver, company_url)

            if about_data:
                about_data['Company Name'] = company_name
                about_data['LinkedIn URL'] = company_url
                about_data.update(people_data)  # Add people data
                results.append(about_data)

    output_df = pd.DataFrame(results)
    output_df.to_csv(output_file, index=False)
    print(f"✅ Data saved to {output_file}")


# Run the scraper
with uc.Chrome(options=chrome_options) as driver:
    driver.set_page_load_timeout(180)
    login(driver)
    input("Log in to LinkedIn manually, then press Enter to continue...")
    process_companies(driver, "data.csv", "output.csv")
    print("✅ Scraping completed successfully!")

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
from fake_useragent import UserAgent
from selenium.common.exceptions import TimeoutException, NoSuchElementException


ua = UserAgent()
chrome_options = uc.ChromeOptions()
chrome_options.headless = False  
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_argument(f"user-agent={ua.random}") 
linkedin_username = os.getenv("LINKEDIN_USER")
linkedin_password = os.getenv("LINKEDIN_PASS")

if not linkedin_username or not linkedin_password:
    raise Exception("LinkedIn credentials not found. Set environment variables first.")


def slow_down():
    time.sleep(random.uniform(3, 8))


def login(driver):
    driver.get("https://www.linkedin.com/login")
    time.sleep(random.uniform(3, 5))

    try:
        email_input = driver.find_element(By.ID, "username")
        password_input = driver.find_element(By.ID, "password")

        email_input.send_keys(linkedin_username)
        password_input.send_keys(linkedin_password)
        password_input.send_keys(Keys.RETURN)

        time.sleep(random.uniform(5, 7))  
    except NoSuchElementException:
        print("❌ Error: Login elements not found!")
        driver.quit()
        exit()


def get_company_url(driver, company_name):
    
    search_url = f"https://www.linkedin.com/search/results/companies/?keywords={company_name.replace(' ', '%20')}"
    try:
        driver.get(search_url)
        time.sleep(random.uniform(3, 6))

        first_result = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//a[contains(@href, '/company/')]"))
        )
        return first_result.get_attribute("href")
    except TimeoutException:
        print(f"⚠ No LinkedIn page found for {company_name}. Skipping...")
        return None  
    except Exception as e:
        print(f"❌ Error fetching LinkedIn page for {company_name}: {e}")
        return None


def scrape_about_section(driver, company_url):
    about_url = company_url + "about/"

    try:
        driver.get(about_url)
        time.sleep(random.uniform(3, 6))  

        
        for _ in range(3):
            driver.execute_script("window.scrollBy(0, 300);")
            time.sleep(random.uniform(2, 4))

    except TimeoutException:
        print(f"⏳ Timeout while loading {about_url}. Skipping...")
        return {}  
    except Exception as e:
        print(f"❌ Error scraping {about_url}: {e}")
        return {}

    def safe_find(xpath, attribute=None):
        
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


def process_companies(driver, data, output_file):
    
    df = pd.read_csv(data)  
    results = []

    for index, row in df.iterrows():
        company_name = row['Company_Name']  
        print(f"🔍 Searching for {company_name} on LinkedIn...")

        company_url = get_company_url(driver, company_name)

        if not company_url:
            print(f"⚠ Skipping {company_name} as it does not exist on LinkedIn.")
            continue  

        about_data = scrape_about_section(driver, company_url)

        if about_data:
            about_data['Company Name'] = company_name
            about_data['LinkedIn URL'] = company_url
            results.append(about_data)

    output_df = pd.DataFrame(results)
    output_df.to_csv(output_file, index=False)
    print(f"✅ Data saved to {output_file}")



with uc.Chrome(options=chrome_options) as driver:
    driver.set_page_load_timeout(180)  

    login(driver)  
    input("Log in to LinkedIn manually, then press Enter to continue...")  
    process_companies(driver, "data.csv", "output.csv")  

    print("✅ Scraping completed successfully!")

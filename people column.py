import os
import time
import random
import pandas as pd
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from fake_useragent import UserAgent
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import json


ua = UserAgent()
chrome_options = uc.ChromeOptions()
chrome_options.headless = False  
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_argument(f"user-agent={ua.random}")  


linkedin_username = os.getenv("LINKEDIN_USER")
linkedin_password = os.getenv("LINKEDIN_PASS")


def slow_down():
    time.sleep(random.uniform(3, 8))


def login(driver):
    
    driver.get("https://www.linkedin.com/login")
    time.sleep(random.uniform(3, 5))
    try:
        email_input = driver.find_element(By.ID, "username")
        password_input = driver.find_element(By.ID, "password")

        if not linkedin_username or not linkedin_password:
            print("❌ Error: LinkedIn username or password is not set!")
            driver.quit()
            exit()

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
    except:
        return None


def scrape_people_section(driver, company_url):
    
    people_url = company_url + "people/"
    driver.get(people_url)
    time.sleep(random.uniform(3, 6))

    # Expand "Show More" buttons
    try:
        show_more_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Show more')]")
        for button in show_more_buttons:
            driver.execute_script("arguments[0].click();", button)
            time.sleep(2)
    except:
        pass

    def extract_data(xpath):
        
        try:
            elements = driver.find_elements(By.XPATH, xpath)
            return {elem.text.split('\n')[0]: int(elem.text.split('\n')[1].replace(",", "")) for elem in elements}
        except:
            return {}

    location_data = extract_data("//h3[contains(text(),'Where they live')]/following-sibling::ul//li")
    job_role_data = extract_data("//h3[contains(text(),'What they do')]/following-sibling::ul//li")

    return {"Where They Live": location_data, "What They Do": job_role_data}


def process_companies(driver, data, output_file):
    
    df = pd.read_csv(data)
    people_data = []

    for index, row in df.iterrows():
        company_name = row['Company_Name']
        print(f"🔍 Searching for {company_name} on LinkedIn...")
        company_url = get_company_url(driver, company_name)

        if company_url:
            print(f"✅ Found LinkedIn page for {company_name}")
            people_info = scrape_people_section(driver, company_url)
            if people_info:
                for location, count in people_info.get("Where They Live", {}).items():
                    people_data.append([company_name, "Where They Live", location, count])
                for role, count in people_info.get("What They Do", {}).items():
                    people_data.append([company_name, "What They Do", role, count])
        else:
            print(f"❌ No LinkedIn page found for {company_name}")

    
    df_people = pd.DataFrame(people_data, columns=["Company", "Category", "Attribute", "Count"])
    df_people.to_csv(output_file, index=False)
    print(f"✅ Data saved successfully to {output_file}")



with uc.Chrome(options=chrome_options) as driver:
    driver.set_page_load_timeout(180)
    login(driver)
    input("Log in to LinkedIn manually, then press Enter to continue...")
    process_companies(driver, "data.csv", "output.csv")
    print("✅ Scraping completed successfully!")

# linkedin_data_collection

This project is focused on automating the collection of company-related data from LinkedIn using Selenium and Undetected ChromeDriver. The script extracts various details about companies but does not include columns for "What They Do" and "Where They Live" in the CSV output. Instead, these details are stored separately in the `people_data.json` file.

## Project Workflow
1. **Setup and Configuration:**
   - The script uses `undetected_chromedriver` to bypass LinkedIn's bot detection.
   - A random User-Agent is generated using the `fake_useragent` library to mimic human browsing.
   - LinkedIn login credentials are fetched from environment variables (`LINKEDIN_USER` and `LINKEDIN_PASS`).

2. **Login to LinkedIn:**
   - The script navigates to the LinkedIn login page.
   - It fills in the username and password.
   - The user is prompted to log in manually for verification before the scraping process continues.

3. **Extracting Company Information:**
   - The script searches for companies based on names provided in `data.csv`.
   - It fetches the LinkedIn URL for each company.
   - The script navigates to the company’s "People" section to extract relevant employee distribution data.

4. **Handling the "People" Section:**
   - The script extracts location-based distribution ("Where They Live") and job role distribution ("What They Do").
   - These details are saved in `people_data.json`.
   - The main output CSV does not include these columns.

5. **Saving Data:**
   - The processed company information (excluding "What They Do" and "Where They Live") is saved in `output.csv`.
   - Additional employee distribution details are saved separately in `people_data.json`.

## Difficulties Faced
- **LinkedIn Anti-Bot Detection:**
  - Using undetected ChromeDriver and random user agents helped mitigate bot detection issues.
  - Taking the XDrive links for the specific data column name from the about page by performing inspect function in chrome and converted the html code to access the column titles over here. 

- **Dynamic Web Elements:**
  - Some sections load asynchronously, requiring the use of `WebDriverWait`.
  - The "Show More" buttons needed to be handled programmatically.

- **Data Extraction Challenges:**
  - Parsing textual data from LinkedIn’s UI was complex due to inconsistent formatting.
  - Some companies had incomplete or missing sections, requiring error handling mechanisms.

## Output Files
1. **`output got.csv`** - Contains general company data excluding "What They Do" and "Where They Live".
2. **`people_data.json`** - Stores structured JSON data for employee location and job role distributions.

While performing the operations to scrap data from what people column I had faced difficulty where I cannot able to generate the entire scraped data of the What they do and Where they live column 

## Conclusion
This project successfully automated LinkedIn data extraction while overcoming multiple challenges related to web scraping and anti-bot measures. The approach ensures that essential company details are stored efficiently, with supplementary data saved separately in JSON format for further analysis.


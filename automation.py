import os
import time
import logging
import pandas as pd

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


# ---------------- LOGGING SETUP ----------------
os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    filename="logs/automation.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


def run_automation(username, password, first_name, last_name, emp_id):
    employee_data = []

    # ---------------- CHROME OPTIONS (CRASH FIX) ----------------
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )

    wait = WebDriverWait(driver, 20)

    try:
        logging.info("Opening OrangeHRM website")
        driver.get("https://opensource-demo.orangehrmlive.com")

        # ---------------- LOGIN ----------------
        wait.until(EC.presence_of_element_located((By.NAME, "username"))).send_keys(username)
        driver.find_element(By.NAME, "password").send_keys(password)
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        logging.info("Login successful")

        # ---------------- NAVIGATE TO PIM ----------------
        wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='PIM']"))).click()
        logging.info("Navigated to PIM")

        # ---------------- ADD EMPLOYEE ----------------
        wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Add']"))).click()

        wait.until(EC.presence_of_element_located((By.NAME, "firstName"))).send_keys(first_name)
        driver.find_element(By.NAME, "lastName").send_keys(last_name)

        emp_id_field = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//label[text()='Employee Id']/../following-sibling::div/input")
            )
        )
        emp_id_field.clear()
        emp_id_field.send_keys(emp_id)

        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        logging.info("Employee saved")

        # ---------------- WAIT FOR SPA TRANSITION ----------------
        wait.until(EC.presence_of_element_located((By.XPATH, "//h6[text()='Personal Details']")))
        time.sleep(3)  # CRITICAL stability wait

        # ---------------- GO TO EMPLOYEE LIST (URL BASED - STABLE) ----------------
        driver.get("https://opensource-demo.orangehrmlive.com/web/index.php/pim/viewEmployeeList")

        wait.until(
            EC.presence_of_element_located((By.XPATH, "//div[@class='oxd-table-body']"))
        )
        logging.info("Employee list loaded")

        # ---------------- EXTRACT EMPLOYEE TABLE ----------------
        rows = driver.find_elements(
            By.XPATH, "//div[@class='oxd-table-body']//div[@role='row']"
        )

        for row in rows:
            cols = row.find_elements(By.XPATH, ".//div[@role='cell']")
            if len(cols) >= 5:
                employee_data.append({
                    "Employee ID": cols[1].text,
                    "First Name": cols[2].text,
                    "Last Name": cols[3].text,
                    "Job Title": cols[4].text
                })

        logging.info(f"Extracted {len(employee_data)} employees")

        # ---------------- EXPORT CSV & EXCEL ----------------
        if employee_data:
            os.makedirs("exports", exist_ok=True)
            df = pd.DataFrame(employee_data)

            # df.to_csv("exports/employees.csv", index=False)
            # df.to_excel("exports/employees.xlsx", index=False)
            from datetime import datetime

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            csv_path = f"exports/employees_{timestamp}.csv"
            excel_path = f"exports/employees_{timestamp}.xlsx"

            df.to_csv(csv_path, index=False)
            df.to_excel(excel_path, index=False)

            logging.info(f"Exported files: {csv_path}, {excel_path}")

            logging.info("Employee data exported to CSV and Excel")

        # ---------------- LOGOUT ----------------
        wait.until(
            EC.element_to_be_clickable((By.CLASS_NAME, "oxd-userdropdown-name"))
        ).click()

        wait.until(
            EC.element_to_be_clickable((By.XPATH, "//a[text()='Logout']"))
        ).click()

        logging.info("Logout successful")

        return "Automation Successful ✅", employee_data

    except Exception as e:
        driver.save_screenshot("error.png")
        logging.exception("Automation failed")
        return f"Automation Failed ❌: {str(e)}", []

    finally:
        driver.quit()

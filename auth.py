import os
import time
import random
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()

SUBDOMAIN = os.getenv("SCHOOL_SUBDOMAIN")
EMAIL = os.getenv("SCHOOL_EMAIL")
PASSWORD = os.getenv("SCHOOL_PASS")
HEADLESS_MODE = os.getenv("HEADLESS", "False").lower() == "true"
TIMEOUT = int(os.getenv("TIMEOUT", 30000))

LOGIN_URL = f"https://{SUBDOMAIN}.myschoolapp.com/app?svcid=edu#login"

def refresh_cookie():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS_MODE)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:147.0) Gecko/20100101 Firefox/147.0"
        )
        page = context.new_page()
        page.set_default_timeout(TIMEOUT)

        print(f"--- Grabbing Cookie ---")
        page.goto(LOGIN_URL)

        # --- STEP 1: BLACKBAUD EMAIL PAGE ---
        # print("1. Filling Blackbaud email...")
        try:
            page.wait_for_selector('input[type="text"], input[type="email"]')
            page.fill('input[type="text"], input[type="email"]', EMAIL)
            
            page.get_by_text("Next", exact=True).click()
        except Exception as e:
            print(f"Warning at Step 1: {e}")

        # --- STEP 2: MICROSOFT PASSWORD PAGE ---
        # print("2. Waiting for Microsoft Password field...")
        try:
            page.wait_for_selector('input[name="passwd"]', state="visible")
            time.sleep(1)
            page.fill('input[name="passwd"]', PASSWORD)
            
            page.click('input[type="submit"]')
        except Exception as e:
            print(f"Failed at Password Step: {e}")
            return

        # --- STEP 3: STAY SIGNED IN ---
        # print("3. Handling 'Stay signed in'...")
        try:
            page.wait_for_selector('input[id="idSIButton9"]', timeout=5000)
            page.click('input[id="idSIButton9"]')
        except:
            print("   (Skipped 'Stay signed in' - not asked)")

        # --- STEP 4: SUCCESS ---
        # print("4. Waiting for homepage...")
        try:
            page.wait_for_url("**/app/**")
            print("Login Success!")
            
            # --- OPTION 1: Save Raw Cookie String ---
            all_cookies = context.cookies()

            cookie_string = "; ".join([f"{c['name']}={c['value']}" for c in all_cookies])
            
            with open("cookie.txt", "w") as f:
                f.write(cookie_string)
            
            print("Saved cookies to 'cookie.txt'")
            
        except Exception as e:
            print(f"Timed out waiting for homepage. Last URL: {page.url}")

        browser.close()

if __name__ == "__main__":
    refresh_cookie()

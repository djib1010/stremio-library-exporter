#!/usr/bin/env python3
"""
Stremio Authentication Key Extractor using Playwright
This script automates the login process and extracts the auth key from localStorage
"""

import asyncio
import os
import json
import logging
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright
from dotenv import load_dotenv


def setup_logging():
    """Setup structured logging with timestamps"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    return logging.getLogger(__name__)


class StremioAuthExtractor:
    def __init__(self, browser_type="chromium", logger=None):
        """Initialize the auth extractor"""
        self.browser_type = browser_type
        self.logger = logger or logging.getLogger(__name__)
        self.email = None
        self.password = None
        self._load_credentials()

    def _load_credentials(self):
        """Load credentials from .env file"""
        load_dotenv()
        self.email = os.getenv("STREMIO_EMAIL")
        self.password = os.getenv("STREMIO_PASSWORD")

        if not self.email or not self.password:
            raise ValueError(
                "Please set STREMIO_EMAIL and STREMIO_PASSWORD in your .env file"
            )

    async def extract_auth_key(self, headless=True):
        """Extract the authentication key from Stremio localStorage"""
        async with async_playwright() as p:
            browser = await self._launch_browser(p, headless)

            try:
                page = await self._create_page(browser)
                await self._navigate_and_login(page)
                return await self._extract_auth_key_from_storage(page)

            except Exception as e:
                self.logger.error(f"Auth extraction failed: {e}")
                raise
            finally:
                await browser.close()

    async def _launch_browser(self, playwright, headless):
        """Launch browser based on specified type"""
        browsers = {
            "firefox": playwright.firefox,
            "webkit": playwright.webkit,
            "chromium": playwright.chromium,
        }
        browser_launcher = browsers.get(self.browser_type, playwright.chromium)
        return await browser_launcher.launch(headless=True) # Change to observe browser actions

    async def _create_page(self, browser):
        """Create a new page with default settings"""
        return await browser.new_page()

    async def _navigate_and_login(self, page):
        """Navigate to Stremio and handle login if needed"""
        self.logger.info("Navigating to Stremio login page")
        await page.goto(
            "https://web.stremio.com/#/intro?form=login", wait_until="networkidle"
        )

        await page.wait_for_selector(
            'div:has-text("Log in"), a[href*="library"]', timeout=30000
        )

        if await page.query_selector('div:has-text("Log in")'):
            self.logger.info("Login required - proceeding with authentication")
            await self._perform_login(page)
        else:
            self.logger.info("Already logged in")

    async def _perform_login(self, page):
        """Handle the complete login process"""
        # Find and click login button
        login_button = await page.wait_for_selector(
            'div.form-button-vyqqj:has-text("Log in")'
        )
        await login_button.click()
        await page.wait_for_timeout(2000)

        # Fill credentials
        await self._fill_credentials(page)

        # Submit form
        submit_button = await page.wait_for_selector(
            'div.form-button-vyqqj:has-text("Log in")'
        )
        await submit_button.click()

        # Wait for login completion
        # Wait for login completion
        self.logger.info("Waiting for login completion")
        # Wait for the login button to disappear or a known element of the logged-in state to appear
        try:
             await page.wait_for_selector('div.form-button-vyqqj:has-text("Log in")', state='hidden', timeout=10000)
             self.logger.info("Login form disappeared")
        except:
             self.logger.warning("Login form might still be visible, checking for success indicators")

        # Consider logged in if we can see the library or user profile, or simply wait for network idle
        await page.wait_for_load_state("networkidle")

    async def _fill_credentials(self, page):
        """Fill email and password fields"""
        # Fill email
        email_input = await page.wait_for_selector('input[placeholder="E-mail"]')
        await email_input.fill(self.email)

        # Fill password
        password_input = await page.wait_for_selector('input[placeholder="Password"]')
        await password_input.fill(self.password)

    async def _extract_auth_key_from_storage(self, page):
        """Extract the auth key from localStorage profile data"""
        self.logger.info("Extracting auth key from localStorage")
        
        # Wait a bit more to ensure localStorage is populated
        await page.wait_for_timeout(3000)
        
        # Extract localStorage data
        storage_data = await page.evaluate("""
            () => {
                const keys = Object.keys(localStorage);
                const data = {};
                keys.forEach(key => {
                    try {
                        data[key] = JSON.parse(localStorage.getItem(key));
                    } catch (e) {
                        data[key] = localStorage.getItem(key);
                    }
                });
                return data;
            }
        """)
                
        # Look for auth dict within profile data in localStorage
        profile_data = None
        for key, value in storage_data.items():
            if isinstance(value, dict) and 'auth' in value:
                profile_data = value
                self.logger.info(f"Found profile data")
                break
                
        if not profile_data:
            raise ValueError("Could not find profile data in localStorage")
        
        # Extract auth key from profile
        if 'auth' not in profile_data:
            raise ValueError("No 'auth' field found in profile data")
        
        auth_data = profile_data['auth']
        if 'key' not in auth_data:
            raise ValueError("No 'key' field found in auth data")
        
        auth_key = auth_data['key']
        self.logger.info(f"Successfully extracted auth key")
        
        return auth_key


async def extract_stremio_auth_key(headless=True, browser_type="chromium"):
    """
    Simple function to extract Stremio auth key and return it
    """
    # Setup minimal logging for internal calls
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    
    # Do not add manual handlers here as it causes duplication when root logger is configured
    # The caller is responsible for configuring logging
    
    extractor = StremioAuthExtractor(browser_type=browser_type, logger=logger)
    return await extractor.extract_auth_key(headless=headless)


async def main():
    """Main function to run the auth extractor"""
    import argparse

    parser = argparse.ArgumentParser(description="Extract Stremio Auth Key")
    parser.add_argument(
        "--browser",
        choices=["chromium", "firefox", "webkit"],
        default="chromium",
        help="Browser to use",
    )

    args = parser.parse_args()
    logger = setup_logging()

    try:
        logger.info("Starting Stremio auth key extraction")
        extractor = StremioAuthExtractor(browser_type=args.browser, logger=logger)
        auth_key = await extractor.extract_auth_key(headless=True)
        logger.info(f"✅ Successfully extracted auth key: {auth_key}")
        print(f"\nAuth Key: {auth_key}")

    except Exception as e:
        logger.error(f"❌ Auth extraction failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)

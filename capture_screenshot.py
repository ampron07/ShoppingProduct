"""Capture the real running app; requires the optional playwright package."""

from pathlib import Path

from playwright.sync_api import sync_playwright


def main():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="msedge", headless=True)
        page = browser.new_page(viewport={"width": 1400, "height": 1200}, device_scale_factor=1)
        page.goto("http://localhost:8501", wait_until="domcontentloaded")
        page.get_by_role("textbox", name="Product keyword").fill("phone")
        page.get_by_role("button", name="Search", exact=True).click()
        page.get_by_text('Results for "phone"', exact=True).wait_for(timeout=30000)
        metrics = page.locator('[data-testid="stMetricValue"]')
        metrics.nth(4).wait_for()
        prices = [float(value.replace("$", "").replace(",", "")) for value in metrics.all_text_contents()]
        assert len(prices) == 5 and prices == sorted(prices), prices
        page.wait_for_function("Array.from(document.images).every(image => image.complete)", timeout=30000)
        page.screenshot(path="website_screenshot.png", full_page=True)
        print(f"Saved {Path('website_screenshot.png').resolve()}")
        print(f"Real result prices: {prices}")
        browser.close()


if __name__ == "__main__":
    main()

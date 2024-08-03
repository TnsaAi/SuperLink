#SuperLink

import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import re

async def main():
    async with async_playwright() as p:
        # Launch a browser (Chromium, Firefox, or WebKit)
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Replace with the actual URL of the Instagram page
        url = 'https://www.instagram.com/leomessi/'
        await page.goto(url)

        # Wait for the 'Follow' button to appear
        await page.wait_for_selector("div[dir='auto']", timeout=10000)

        # Get the page content after JavaScript execution
        content = await page.content()
        await browser.close()

        # Parse the HTML content
        soup = BeautifulSoup(content, 'html.parser')

        # Find the first div containing the text 'Follow'
        follow_button = soup.find('div', string='Follow')

        # Convert the follow button element to a string
        if follow_button:
            result = follow_button.prettify()  # Pretty print the HTML
        else:
            result = 'Follow button not found'

        return result


def findTheClassName(inp):
    divided = inp.split('class=')

    followPart = None
    for element in divided:
        if 'Follow' in element:
            followPart = element
            break
    
    # Define the regular expression pattern
    pattern = r'"([^"]*)"'

    # Search for the pattern
    match = re.search(pattern, followPart)

    # Check if a match was found
    if match:
        # Extract the first captured group
        first_substring = match.group(1)
        result = re.sub(r' ', '.', first_substring)
        return 'div.' + result
    else:
        return None
    

# Run the async function and get the result
inp = asyncio.run(main())


print(findTheClassName(inp))

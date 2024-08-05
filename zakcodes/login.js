const puppeteer = require('puppeteer');

(async () => {
  const username = 'k_z.a.k'; // Replace with your Instagram username
  const password = 'Abcd123!@#'; // Replace with your Instagram password

  const browser = await puppeteer.launch({
    headless: false, // Run in headless mode for backend automation
    userDataDir: './new_user_data', // Change to a different directory
  });

  const page = await browser.newPage();

  // Enable request interception
  await page.setRequestInterception(true);

  // Handle request interception for cookies consent dialog
  page.on('request', async (req) => {
    if (req.url().includes('consent/')) {
      await req.respond({
        status: 200,
        contentType: 'text/plain',
        body: 'Opted out of optional cookies',
      });
    } else {
      req.continue();
    }
  });

  // Navigate to Instagram login page
  await page.goto('https://www.instagram.com/accounts/login/', { waitUntil: 'networkidle2' });

  // Wait for the login page to load
  await page.waitForSelector('input[name="username"]');

  // Take screenshot before filling credentials
  await page.screenshot({ path: '1_before_login.png' });

  // Fill in username and password and login
  await page.type('input[name="username"]', username);
  await page.type('input[name="password"]', password);

  // Click login button
  await page.click('button[type="submit"]');

  // Wait for navigation after login
  await page.waitForNavigation({ waitUntil: 'networkidle2' });

  // Take screenshot after successful login
  await page.screenshot({ path: '2_after_login.png' });

  // For testing purposes, let's wait for 10 seconds before closing the browser
  await page.waitForTimeout(10000);

  await browser.close();
})();
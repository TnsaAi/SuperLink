from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import threading

def automate_follow(credential, link):
    options = Options()
    options.headless = True
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        if credential.platform.lower() == 'twitter':
            driver.get('https://twitter.com/login')
            driver.find_element(By.NAME, 'session[username_or_email]').send_keys(credential.username)
            driver.find_element(By.NAME, 'session[password]').send_keys(credential.password)
            driver.find_element(By.XPATH, '//*[text()="Log in"]').click()
            driver.get(link)
            driver.find_element(By.XPATH, '//*[text()="Follow"]').click()
        elif credential.platform.lower() == 'facebook':
            driver.get('https://www.facebook.com/login')
            driver.find_element(By.NAME, 'email').send_keys(credential.username)
            driver.find_element(By.NAME, 'pass').send_keys(credential.password)
            driver.find_element(By.NAME, 'login').click()
            driver.get(link)
            driver.find_element(By.XPATH, '//*[text()="Follow"]').click()
        # Repeat for other platforms
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        driver.quit()

def follow_all(credentials, links):
    threads = []
    for credential in credentials:
        for link in links:
            if credential.platform.lower() == link.platform.lower():
                thread = threading.Thread(target=automate_follow, args=(credential, link.link))
                threads.append(thread)
                thread.start()
    for thread in threads:
        thread.join()

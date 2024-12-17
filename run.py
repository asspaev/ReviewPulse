from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException, TimeoutException

import src.engine as engine
from settings import links_catalogs



if __name__ == '__main__':
    service = Service(executable_path=ChromeDriverManager().install())
    for link_catalog in links_catalogs:
        engine.collect_catalog(service=service, link_catalog=link_catalog)

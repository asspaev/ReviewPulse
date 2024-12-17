import requests
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import os
import time
from selenium.webdriver.chromium.webdriver import ChromiumDriver
from typing import Tuple

import src.utils as utils
import src.models.requests as sql
from settings import SIZE_COUNT_PRODUCTS, SIZE_COUNT_REVIEWS, PATH_DATA


def collect_catalog(service: Service, link_catalog: str) -> None:
    """Парсинг каталога"""
    # TODO: Вставить проверку на статус каталога или вынести это в отдельную функцию
    print(f'Начат парсинг каталога {link_catalog}')
    driver, wait, actions = utils.open_chrome(service)
    driver.set_window_size(1280, 1000)
    driver.get(link_catalog)
    sql.add_catalog(catalog_link=link_catalog, collected=False, analyzed=False)
    links_products = get_links_to_products((driver, wait, actions), link_catalog)
    catalog_id = sql.get_catalog_id_by_link(catalog_link=link_catalog)
    for link_product in links_products:
        collect_product((driver, wait, actions), link_product=link_product, catalog_id=catalog_id)
    sql.update_catalog_collected(catalog_id=catalog_id, collected=True)
    print(f'Парсинг каталога {link_catalog} завершён успешно!')

def get_links_to_products(engine_chrome: Tuple[ChromiumDriver, WebDriverWait, ActionChains], link_catalog: str) -> list:
    """Сбор ссылок на продукты из каталога"""
    print(f'Начат сбор ссылок на продукты для текущего каталога')
    driver, wait, actions = engine_chrome
    links_products = []  # тут храним ссылки на страницы товаров
    cursor_page = 1  # указатель на страницу
    cursor_product = 1  # указатель на товар
    # Сбор ссылок на товары из категории
    for i in range(1, SIZE_COUNT_PRODUCTS + 1):
        locator = ('xpath', f'(//div[@class="product-card__wrapper"]/a)[{cursor_product}]')  # определить ссылку на продукт
        try:
            product = wait.until(ec.visibility_of_element_located(locator))  # найти продукт
        except TimeoutException:
            cursor_product = 1
            cursor_page += 1
            driver.get(f'{link_catalog}?sort=popular&page={cursor_page}')
            locator = ('xpath', f'(//div[@class="product-card__wrapper"]/a)[{cursor_product}]')  # определить ссылку на продукт
            product = wait.until(ec.visibility_of_element_located(locator))  # найти продукт
        links_products.append(product.get_attribute('href'))  # сохранить ссылку на продукт
        actions.move_to_element(product).perform()  # прокрутить до продукта
        driver.execute_script("window.scrollBy(0, 350);")
        cursor_product += 1
    print(f'Сбор ссылок на продукты успешно завершён!')
    return links_products

def collect_product(engine_chrome: Tuple[ChromiumDriver, WebDriverWait, ActionChains], link_product: str, catalog_id: int) -> None:
    """Сбор информации о товаре"""
    print(f'Начат парсинг товара {link_product}')
    driver, wait, actions = engine_chrome
    driver.get(link_product)  # открыть страницу товара
    product_name = wait.until(ec.visibility_of_element_located(('xpath', '//h1[@class="product-page__title"]'))).text  # получить название товара
    product_article = wait.until(ec.visibility_of_element_located(('xpath', '//span[@id="productNmId"]'))).text  # получить артикль товара
    product_rating = wait.until(ec.visibility_of_element_located(('xpath', '//span[contains(@class, "product-review__rating")]'))).text.replace(',', '.')  # получить цену товара
    count_reviews = collect_reviews((driver, wait, actions), product_article=product_article)
    sql.add_product(product_article=product_article, catalog_id=catalog_id,
                    name=product_name, rating=product_rating, count_reviews=count_reviews)
    print(f'Парсинг товара успешно завершён!')

def collect_reviews(engine_chrome: Tuple[ChromiumDriver, WebDriverWait, ActionChains], product_article: int) -> int:
    """Сбор отзывов товаров"""
    print(f'Начат парсинг отзывов для {product_article}')
    driver, wait, actions = engine_chrome
    driver.get(f'https://www.wildberries.ru/catalog/{product_article}/feedbacks')  # открываем страницу с отзывами
    utils.open_optimal_reviews(driver=driver)
    for counter_review in range(1, SIZE_COUNT_REVIEWS + 1):  # парсинг отзывов
        prefix = f'(//ul[@class="comments__list"]/li)[{counter_review}]'
        locator = ('xpath', f'(//ul[@class="comments__list"]/li)[{counter_review}]')  # определить ссылку на отзыв
        try:
            review = wait.until(ec.visibility_of_element_located(locator))  # получить элемент с отзывом
        except TimeoutException:  # если отзывы кончились
            counter_review -= 1
            break
        review_text_all = wait.until(ec.visibility_of_element_located(('xpath', f'{prefix}//div[@class="feedback__content"]'))).text  # получить текст отзыва
        review_rating = wait.until(ec.visibility_of_element_located(('xpath', f'{prefix}//span[contains(@class, "stars-line")]'))).get_attribute('class')[-1:]  # получить рейтинг отзыв
        review_text_plus, review_text_minus, review_text_comment = utils.split_review(text_review=review_text_all)
        sql.add_review(product_article=product_article, rating=review_rating, text_all=review_text_all,
                       text_plus=review_text_plus, text_minus=review_text_minus, text_comment=review_text_comment)
        actions.move_to_element(review).perform()  # прокрутить до отзыва
        driver.execute_script("window.scrollBy(0, 350);")  # прокрутить вниз на 350px
    print(f'Парсинг отзывов для {product_article} успешно завершён!')
    return counter_review
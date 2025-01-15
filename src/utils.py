from selenium import webdriver
from sqlalchemy.orm import Session
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chromium.webdriver import ChromiumDriver
from selenium.webdriver.common.by import By
from typing import Tuple
import re
from pandas import DataFrame
import string

import src.models.requests as sql
from settings import SIZE_COUNT_REVIEWS


def open_chrome(service: Service) -> Tuple[ChromiumDriver, WebDriverWait, ActionChains]:
    """Открыть chrome через selenium"""
    driver = webdriver.Chrome(service=service)
    wait = WebDriverWait(driver, 15, poll_frequency=1)
    actions = ActionChains(driver)
    return driver, wait, actions

def get_catalog_id(session: Session, link_catalog: str) -> int:
    """Получить id каталога"""
    return sql.get_catalog_id_by_link(session=session, catalog_link=link_catalog)

def split_review(text_review: str) -> Tuple[str, str, str]:
    """Разделить отзыв на Достоинства, Недостатки и Комментарий"""
    # Убедимся, что входные данные являются строкой
    if not isinstance(text_review, str):
        text_review = ""  # Преобразуем в пустую строку, если это не строка

    # Регулярные выражения для поиска каждого компонента
    plus_pattern = r"Достоинства:\s*(.*?)(?=\n|$)"
    minus_pattern = r"Недостатки:\s*(.*?)(?=\n|$)"
    comment_pattern = r"Комментарий:\s*(.*?)(?=\n|$)"
    
    # Поиск компонентов с использованием регулярных выражений
    review_plus = re.search(plus_pattern, text_review)
    review_minus = re.search(minus_pattern, text_review)
    review_comment = re.search(comment_pattern, text_review)

    # Если не найдены стандартные комментарии, всё, что не в plus и minus, считаем за комментарий
    if not review_comment:
        review_comment = re.search(r"^(?!Достоинства:|Недостатки:)(.*)", text_review.strip())
    
    # Получаем значения найденных компонентов или "Нет", если они отсутствуют
    review_text_plus = review_plus.group(1) if review_plus else 'Нет'
    review_text_minus = review_minus.group(1) if review_minus else 'Нет'
    review_text_comment = review_comment.group(1) if review_comment else 'Нет'
    
    return review_text_plus, review_text_minus, review_text_comment

def get_count_current_article_reviews(driver: ChromiumDriver) -> int:
    """Получить кол-во отзывов для данного артикля"""
    try:
        # Ожидаем, пока элемент станет видимым на странице
        element = WebDriverWait(driver, 15, poll_frequency=1).until(
            ec.visibility_of_element_located((By.XPATH, "//li[@class='product-feedbacks__tab']//span[@class='product-feedbacks__count']"))
        )
        # Получаем текст из найденного элемента и преобразуем его в число
        feedback_count = int(element.text.strip())
        return feedback_count
    except Exception as e:
        # Возвращаем 0, если элемент не найден или возникла ошибка
        return 0
    
def open_optimal_reviews(driver: ChromiumDriver) -> None:
    """Открыть оптимальный список отзывов"""
    count_current_article_reviews = get_count_current_article_reviews(driver=driver)
    if count_current_article_reviews > (SIZE_COUNT_REVIEWS / 3):
        # Ожидаем, пока элемент станет кликабельным
        element = WebDriverWait(driver, 15, poll_frequency=1).until(
            ec.element_to_be_clickable((By.XPATH, "//li[@class='product-feedbacks__tab']//span[@class='product-feedbacks__count']"))
        )
        # Нажимаем на элемент
        element.click()

def extract_product_article(url: str) -> int:
    """Извлечь product_article из URL."""
    match = re.search(r'/catalog/(\d+)/', url)
    if match:
        return int(match.group(1))
    else:
        raise ValueError("Не удалось извлечь product_article из URL.")

def get_clean_reviews(reviews_data: list) -> DataFrame:
    """Извлечь отзывы без служебной информации"""
    cleaned_reviews = []
    for review in reviews_data:
        cleaned_review = {
            'product_article': review['product_article'],
            'rating': review['rating'],
            'text_plus': review['text_plus'],
            'text_comment': review['text_comment'],
            'text_all': review['text_all'],
            'review_id': review['review_id'],
            'text_minus': review['text_minus']
        }
        cleaned_reviews.append(cleaned_review)
    return cleaned_reviews

def clean_text(text: str) -> str:
    """Приведение текста к нижнему регистру и удаление знаков препинания"""
    if isinstance(text, str):
        return text.lower().translate(str.maketrans('', '', string.punctuation))
    return text
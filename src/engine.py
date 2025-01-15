import requests
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.common.exceptions import StaleElementReferenceException
import os
import docker
import time
from collections import Counter
import pandas as pd
from pandas import DataFrame
from selenium.webdriver.chromium.webdriver import ChromiumDriver
from typing import Tuple

import matplotlib.pyplot as plt
from wordcloud import WordCloud
from nltk.corpus import stopwords

import src.utils as utils
import src.models.requests as sql
from settings import SIZE_COUNT_PRODUCTS, SIZE_COUNT_REVIEWS, PATH_DATA


def collect_catalog(service: Service, link_catalog: str) -> None:
    """Парсинг каталога"""
    print(f'Начат парсинг каталога {link_catalog}')
    catalog_id = sql.get_catalog_id_by_link(catalog_link=link_catalog)
    count_collected = sql.get_product_count_by_catalog_id(catalog_id=catalog_id)
    if count_collected > 0:
        print(f'Обнаружен ранее обрабатываемый каталог. Обработано {count_collected}/{SIZE_COUNT_PRODUCTS}')
        if count_collected == SIZE_COUNT_PRODUCTS:
            print('Этот каталог уже спарсен!')
    driver, wait, actions = utils.open_chrome(service)
    driver.set_window_size(1280, 1000)
    driver.get(link_catalog)
    if catalog_id is None:
        sql.add_catalog(catalog_link=link_catalog, collected=False, analyzed=False)
    links_products = get_links_to_products((driver, wait, actions), link_catalog, count_parse=SIZE_COUNT_REVIEWS - count_collected)
    catalog_id = sql.get_catalog_id_by_link(catalog_link=link_catalog)
    for link_product in links_products:
        collect_product((driver, wait, actions), link_product=link_product, catalog_id=catalog_id)
    sql.update_catalog_collected(catalog_id=catalog_id, collected=True)
    print(f'Парсинг каталога {link_catalog} завершён успешно!')

def get_links_to_products(engine_chrome: Tuple[ChromiumDriver, WebDriverWait, ActionChains], link_catalog: str, count_parse: int) -> list:
    """Сбор ссылок на продукты из каталога"""
    print(f'Начат сбор ссылок на продукты для текущего каталога')
    driver, wait, actions = engine_chrome
    links_products = []  # тут храним ссылки на страницы товаров
    cursor_product = 1  # указатель на товар
    cursor_page = 1
    # Сбор ссылок на товары из категории
    for _ in range(1, count_parse + 1):
        is_new_product = False
        while is_new_product == False:
            locator = ('xpath', f'(//div[@class="product-card__wrapper"]/a)[{cursor_product}]')  # определить ссылку на продукт
            try:
                product = wait.until(ec.visibility_of_element_located(locator))  # найти продукт
            except TimeoutException:
                cursor_product = 1
                cursor_page += 1
                driver.get(f'{link_catalog}?sort=popular&page={cursor_page}')
                locator = ('xpath', f'(//div[@class="product-card__wrapper"]/a)[{cursor_product}]')  # определить ссылку на продукт
                product = wait.until(ec.visibility_of_element_located(locator))  # найти продукт
            link_product = product.get_attribute('href')
            article = utils.extract_product_article(url=link_product)
            if not sql.check_product_article_exists(product_article=article):
                links_products.append(link_product)  # сохранить ссылку на продукт
                is_new_product = True
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
    if product_rating != 'Нет оценок':
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
        try:
            review_text_all = wait.until(ec.visibility_of_element_located(('xpath', f'{prefix}//div[@class="feedback__content"]'))).text  # получить текст отзыва
            review_text_plus, review_text_minus, review_text_comment = utils.split_review(text_review=review_text_all)
        except StaleElementReferenceException:
            review_text_all = ''
            review_text_plus, review_text_minus, review_text_comment = 'Нет', 'Нет', 'Нет'
        review_rating = wait.until(ec.visibility_of_element_located(('xpath', f'{prefix}//span[contains(@class, "stars-line")]'))).get_attribute('class')[-1:]  # получить рейтинг отзыв
        sql.add_review(product_article=product_article, rating=review_rating, text_all=review_text_all,
                       text_plus=review_text_plus, text_minus=review_text_minus, text_comment=review_text_comment)
        try:
            actions.move_to_element(review).perform()  # прокрутить до отзыва
            driver.execute_script("window.scrollBy(0, 350);")  # прокрутить вниз на 350px
        except StaleElementReferenceException:
            break
    print(f'Парсинг отзывов для {product_article} успешно завершён!')
    return counter_review

def data_analysis(catalog_link: str):
    """Анализ данных каталога"""
    print(f'Начат анализ каталога {catalog_link}')
    # Подгрузка данных
    df = data_load(catalog_link=catalog_link)
    df_rating_1 = df[df['rating'] == 1]
    df_rating_2 = df[df['rating'] == 2]
    df_rating_3 = df[df['rating'] == 3]
    df_rating_4 = df[df['rating'] == 4]
    df_rating_5 = df[df['rating'] == 5]
    dfs_ratings = [df_rating_1, df_rating_2, df_rating_3, df_rating_4, df_rating_5]
    print(f'Получено {df_rating_1.shape[0]} отзывов с рейтингом 1')
    print(f'Получено {df_rating_2.shape[0]} отзывов с рейтингом 2')
    print(f'Получено {df_rating_3.shape[0]} отзывов с рейтингом 3')
    print(f'Получено {df_rating_4.shape[0]} отзывов с рейтингом 4')
    print(f'Получено {df_rating_5.shape[0]} отзывов с рейтингом 5')
    create_and_save_wordscloud(dfs_ratings=dfs_ratings, catalog=catalog_link.replace('https://www.', '').replace('/', '_').replace('?', '_'))
    create_and_save_bigramscloud(dfs_ratings=dfs_ratings, catalog=catalog_link.replace('https://www.', '').replace('/', '_').replace('?', '_'))
    print(f'Анализ каталога {catalog_link} успешно завершён!')

def data_load(catalog_link: str):
    """Загрузить данные и вернуть в виде DataFrame"""
    catalog_id = sql.get_catalog_id_by_link(catalog_link=catalog_link)
    # Получить все артикли товаров каталога
    product_articles = sql.get_product_articles_by_catalog_id(catalog_id=catalog_id)
    columns = ['product_article', 'rating', 'text_plus', 'text_comment', 'text_all', 'review_id', 'text_minus']
    df_reviews = pd.DataFrame(columns=columns)
    for article in product_articles:
        reviews = sql.get_reviews_by_product_article(product_article=article)
        cleaned_reviews = utils.get_clean_reviews(reviews_data=reviews)
        new_reviews_df = pd.DataFrame(cleaned_reviews)
        df_reviews = pd.concat([df_reviews, new_reviews_df], ignore_index=True)
    return df_reviews

def create_and_save_wordscloud(dfs_ratings: DataFrame, catalog: str) -> None:
    """Создать и сохранить wordscloud"""
    for i in range(0, len(dfs_ratings)): 
        for col in dfs_ratings[i].columns:
            dfs_ratings[i][col] = dfs_ratings[i][col].apply(utils.clean_text)
    # Загружаем стоп-слова
    stop_words = set(stopwords.words('russian'))

    # Функция для удаления стоп-слов
    def remove_stopwords(text):
        words = text.split()
        filtered_words = [word for word in words if word.lower() not in stop_words]
        return ' '.join(filtered_words)

    # Функция для генерации облака слов с ограничением по количеству слов и размерам
    def generate_wordcloud(text, width=800, height=800, max_words=100):
        return WordCloud(width=width, height=height, background_color='white', max_words=max_words).generate(text)

    # Функция для получения топ-10 слов
    def get_top_words(text, top_n=10):
        words = text.split()
        counter = Counter(words)
        return counter.most_common(top_n)

    # Папка для сохранения изображений
    output_dir = f"data/results/{catalog}/wordclouds"
    os.makedirs(output_dir, exist_ok=True)

    # Настройка размера для сетки изображений
    fig, axes = plt.subplots(len(dfs_ratings), 4, figsize=(20, len(dfs_ratings) * 5))

    # Перебор датафреймов и столбцов
    for i, df in enumerate(dfs_ratings):
        texts = [
            ' '.join(df['text_plus'].dropna()),  # review_text_plus
            ' '.join(df['text_minus'].dropna()),  # review_text_minus
            ' '.join(df['text_comment'].dropna()),  # review_text_comment
            ' '.join(df['text_plus'].dropna()) + ' ' + ' '.join(df['text_minus'].dropna()) + ' ' + ' '.join(df['text_comment'].dropna())  # Все вместе
        ]
        
        # Удаляем стоп-слова из текстов
        cleaned_texts = [remove_stopwords(text) for text in texts]
        
        titles = ['Достоинства', 'Недостатки', 'Комментарий', 'Весь отзыв']

        # Создание словаря для хранения данных по рейтингу и категориям
        dataframes = {}
        
        # Заполнение DataFrame для каждой категории и рейтинга
        for j, cleaned_text in enumerate(cleaned_texts):
            top_words = get_top_words(cleaned_text)
            category = titles[j]
            dataframes[category] = pd.DataFrame(top_words, columns=["Word", f"Top 10 Words (Category: {category})"])

        # Сохранение в Excel
        excel_filename = f"data/results/{catalog}/top_words_rating_{i+1}.xlsx"
        with pd.ExcelWriter(excel_filename) as writer:
            for sheet_name, df in dataframes.items():
                df.to_excel(writer, sheet_name=str(sheet_name))  # Преобразуем sheet_name в строку, чтобы избежать ошибок

        # Сохранение каждого облака
        for j, cleaned_text in enumerate(cleaned_texts):
            wordcloud = generate_wordcloud(cleaned_text)
            
            # Сохранение каждого облака в отдельный файл
            wordcloud_file = os.path.join(output_dir, f'wordcloud_rating_{i+1}_part_{j+1}.png')
            wordcloud.to_file(wordcloud_file)
            
            # Отображение на сетке
            axes[i, j].imshow(wordcloud, interpolation='bilinear')
            axes[i, j].axis('off')
            axes[i, j].set_title(f'{titles[j]} (Оценка {i+1}/5)')

    # Уменьшаем пространство между графиками
    plt.subplots_adjust(wspace=0.1, hspace=0.3)

    # Сохранение итоговой сетки в файл
    final_grid_file = os.path.join(output_dir, "wordcloud_grid.png")
    plt.savefig(final_grid_file, dpi=300, bbox_inches='tight')

    # Отображение облаков слов
    # plt.tight_layout()
    # plt.show()

def create_and_save_bigramscloud(dfs_ratings: DataFrame, catalog: str) -> None:
    """Создать и сохранить bigramscloud"""
    for i in range(0, len(dfs_ratings)): 
        for col in dfs_ratings[i].columns:
            dfs_ratings[i][col] = dfs_ratings[i][col].apply(utils.clean_text)
    
    # Загружаем стоп-слова
    stop_words = set(stopwords.words('russian'))

    # Функция для удаления стоп-слов
    def remove_stopwords(text):
        words = text.split()
        filtered_words = [word for word in words if word.lower() not in stop_words]
        return ' '.join(filtered_words)

    # Функция для создания биграмм
    def generate_bigrams(text):
        tokens = text.split()
        bigrams = [' '.join(pair) for pair in zip(tokens, tokens[1:])]
        return bigrams

    # Функция для генерации облака биграмм
    def generate_bigramscloud(bigram_freqs, width=800, height=800, max_words=100):
        return WordCloud(width=width, height=height, background_color='white', max_words=max_words).generate_from_frequencies(bigram_freqs)

    # Папка для сохранения изображений
    output_dir = f"data/results/{catalog}/bigramsclouds"
    os.makedirs(output_dir, exist_ok=True)

    # Настройка размера для сетки изображений
    fig, axes = plt.subplots(len(dfs_ratings), 4, figsize=(20, len(dfs_ratings) * 5))

    # Перебор датафреймов и столбцов
    for i, df in enumerate(dfs_ratings):
        texts = [
            ' '.join(df['text_plus'].dropna()),  # review_text_plus
            ' '.join(df['text_minus'].dropna()),  # review_text_minus
            ' '.join(df['text_comment'].dropna()),  # review_text_comment
            ' '.join(df['text_plus'].dropna()) + ' ' + ' '.join(df['text_minus'].dropna()) + ' ' + ' '.join(df['text_comment'].dropna())  # Все вместе
        ]
        
        # Удаляем стоп-слова из текстов
        cleaned_texts = [remove_stopwords(text) for text in texts]

        titles = ['Достоинства', 'Недостатки', 'Комментарий', 'Весь отзыв']

        # Создание словаря для хранения данных по рейтингу и категориям
        dataframes = {}

        # Создание таблиц топ-биграмм
        for j, cleaned_text in enumerate(cleaned_texts):
            bigrams = generate_bigrams(cleaned_text)
            bigram_freqs = Counter(bigrams)
            top_bigrams = bigram_freqs.most_common(10)
            category = titles[j]
            dataframes[category] = pd.DataFrame(top_bigrams, columns=["Bigram", f"Top 10 Bigrams (Category: {category})"])

        # Сохранение в Excel
        excel_filename = f"data/results/{catalog}/top_bigrams_rating_{i+1}.xlsx"
        with pd.ExcelWriter(excel_filename) as writer:
            for sheet_name, df in dataframes.items():
                df.to_excel(writer, sheet_name=str(sheet_name))  # Преобразуем sheet_name в строку, чтобы избежать ошибок

        # Сохранение каждого облака
        for j, cleaned_text in enumerate(cleaned_texts):
            bigrams = generate_bigrams(cleaned_text)
            bigram_freqs = Counter(bigrams)
            bigramscloud = generate_bigramscloud(bigram_freqs)
            
            # Сохранение каждого облака в отдельный файл
            bigramscloud_file = os.path.join(output_dir, f'bigramscloud_rating_{i+1}_part_{j+1}.png')
            bigramscloud.to_file(bigramscloud_file)
            
            # Отображение на сетке
            axes[i, j].imshow(bigramscloud, interpolation='bilinear')
            axes[i, j].axis('off')
            axes[i, j].set_title(f'{titles[j]} (Оценка {i+1}/5)')

    # Уменьшаем пространство между графиками
    plt.subplots_adjust(wspace=0.1, hspace=0.3)

    # Сохранение итоговой сетки в файл
    final_grid_file = os.path.join(output_dir, "bigramscloud_grid.png")
    plt.savefig(final_grid_file, dpi=300, bbox_inches='tight')

    # Отображение облаков биграмм
    # plt.tight_layout()
    # plt.show()

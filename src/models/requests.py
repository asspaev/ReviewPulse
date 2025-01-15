from sqlalchemy import select, func, update
from sqlalchemy.orm import Session
from src.models.models import Catalog, Product, Review, Analysis, main_engine

def create_session():
    return Session(main_engine)

def add_catalog(catalog_link: str, collected: bool, analyzed: bool):
    """Добавить каталог в БД"""
    session = create_session()
    new_catalog = Catalog(
        catalog_link=catalog_link, 
        collected=collected, 
        analyzed=analyzed
    )
    session.add(new_catalog)
    session.commit()
    session.close()

def get_product_count_by_catalog_id(catalog_id: int) -> int:
    """Получить количество продуктов для заданного 'catalog_id'."""
    session = create_session()
    result = session.execute(
        select(func.count()).select_from(Product).where(Product.catalog_id == catalog_id)
    ).scalar_one()
    session.close()
    return result

def add_product(product_article: int, catalog_id: int, name: str, rating: float, count_reviews: int):
    """Добавить товар в БД"""
    session = create_session()
    new_product = Product(
        product_article=product_article, 
        catalog_id=catalog_id,
        name=name, 
        rating=rating, 
        count_reviews=count_reviews
    )
    session.add(new_product)
    session.commit()
    session.close()

def add_review(product_article: int, rating: int, text_all: str = None, text_plus: str = None, text_minus: str = None, text_comment: str = None):
    """Добавить отзыв в БД"""
    session = create_session()
    new_review = Review(
        product_article=product_article, 
        rating=rating, 
        text_all=text_all, 
        text_plus=text_plus, 
        text_minus=text_minus, 
        text_comment=text_comment
    )
    session.add(new_review)
    session.commit()
    session.close()

def add_analysis(word: str, frequency: float, df_index: str, column: str):
    session = create_session()
    new_analysis = Analysis(
        word=word, 
        frequency=frequency, 
        df_index=df_index, 
        column=column
    )
    session.add(new_analysis)
    session.commit()
    session.close()

def update_catalog_collected(catalog_id: int, collected: bool):
    """Обновить статус каталога (сбор данных)"""
    session = create_session()
    stmt = update(Catalog).where(Catalog.catalog_id == catalog_id).values(collected=collected)
    session.execute(stmt)
    session.commit()
    session.close()

def update_catalog_analyzed(catalog_id: int, analyzed: bool):
    """Обновить статус каталога (анализ)"""
    session = create_session()
    stmt = update(Catalog).where(Catalog.catalog_id == catalog_id).values(analyzed=analyzed)
    session.execute(stmt)
    session.commit()
    session.close()

def check_product_article_exists(product_article: int) -> bool:
    """Проверить наличие 'product_article' в таблице 'products'."""
    session = create_session()
    result = session.execute(
        select(Product.product_id).where(Product.product_article == product_article)
    ).scalar_one_or_none()
    session.close()
    return result is not None

def get_catalog_id_by_link(catalog_link: str):
    """Получить id каталога по его ссылке"""
    session = create_session()
    catalog = session.query(Catalog).filter(Catalog.catalog_link == catalog_link).first()
    session.close()
    if catalog:
        return catalog.catalog_id
    return None

def is_product_exists(product_id: int) -> bool:
    """Получить информацию о наличии товара в БД"""
    session = create_session()
    product = session.query(Product).filter(Product.product_id == product_id).first()
    session.close()
    return product is not None

def get_product_articles_by_catalog_id(catalog_id: int) -> list:
    """Возвращает массив product_article для заданного catalog_id."""
    session = create_session()
    try:
        result = session.query(Product.product_article).filter(Product.catalog_id == catalog_id).all()
        # Извлекаем product_article из результатов запроса
        product_articles = [row[0] for row in result]
        return product_articles
    finally:
        session.close()

def get_reviews_by_product_article(product_article: str, rating: int = None) -> list:
    """Возвращает массив записей из таблицы reviews для заданного product_article с указанным рейтингом"""
    session = create_session()
    try:
        query = session.query(Review).filter(Review.product_article == product_article)
        
        # Если указан rating, добавляем фильтр
        if rating is not None:
            query = query.filter(Review.rating == rating)
        
        result = query.all()
        return [review.__dict__ for review in result]
    finally:
        session.close()

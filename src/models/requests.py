from sqlalchemy import update
from sqlalchemy.orm import Session
from src.models.models import Catalog, Product, Review, Analysis, main_engine

# Create a session for database interaction
def create_session():
    return Session(main_engine)

# Functions for inserting new data into each table
def add_catalog(catalog_link: str, collected: bool, analyzed: bool):
    session = create_session()
    new_catalog = Catalog(
        catalog_link=catalog_link, 
        collected=collected, 
        analyzed=analyzed
    )
    session.add(new_catalog)
    session.commit()
    session.close()

def add_product(product_article: int, catalog_id: int, name: str, rating: float, count_reviews: int):
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

# Functions for updating the 'collected' and 'analyzed' columns in the 'catalogs' table
def update_catalog_collected(catalog_id: int, collected: bool):
    session = create_session()
    stmt = update(Catalog).where(Catalog.catalog_id == catalog_id).values(collected=collected)
    session.execute(stmt)
    session.commit()
    session.close()

def update_catalog_analyzed(catalog_id: int, analyzed: bool):
    session = create_session()
    stmt = update(Catalog).where(Catalog.catalog_id == catalog_id).values(analyzed=analyzed)
    session.execute(stmt)
    session.commit()
    session.close()

# Функция для получения catalog_id по catalog_link
def get_catalog_id_by_link(catalog_link: str):
    session = create_session()
    catalog = session.query(Catalog).filter(Catalog.catalog_link == catalog_link).first()
    session.close()
    if catalog:
        return catalog.catalog_id
    return None

# Функция для проверки наличия продукта по product_article
def is_product_exists(product_id: int) -> bool:
    session = create_session()
    product = session.query(Product).filter(Product.product_id == product_id).first()
    session.close()
    return product is not None

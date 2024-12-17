from sqlalchemy import update
from sqlalchemy.orm import Session
from src.models import Catalog, Product, Review, Analysis, main_engine

# Create a session for database interaction
def create_session():
    return Session(main_engine)

# Functions for inserting new data into each table
def add_catalog(session: Session, catalog_id: int, catalog_link: str, collected: bool, analyzed: bool):
    new_catalog = Catalog(
        catalog_id=catalog_id, 
        catalog_link=catalog_link, 
        collected=collected, 
        analyzed=analyzed
    )
    session.add(new_catalog)
    session.commit()

def add_product(session: Session, product_article: int, catalog_id: int, name: str, rating: float, count_reviews: int):
    new_product = Product(
        product_article=product_article, 
        catalog_id=catalog_id, 
        name=name, 
        rating=rating, 
        count_reviews=count_reviews
    )
    session.add(new_product)
    session.commit()

def add_review(session: Session, review_id: int, product_article: int, rating: int, text_all: str = None, text_plus: str = None, text_minus: str = None, text_comment: str = None):
    new_review = Review(
        review_id=review_id, 
        product_article=product_article, 
        rating=rating, 
        text_all=text_all, 
        text_plus=text_plus, 
        text_minus=text_minus, 
        text_comment=text_comment
    )
    session.add(new_review)
    session.commit()

def add_analysis(session: Session, word: str, frequency: float, df_index: str, column: str):
    new_analysis = Analysis(
        word=word, 
        frequency=frequency, 
        df_index=df_index, 
        column=column
    )
    session.add(new_analysis)
    session.commit()

# Functions for updating the 'collected' and 'analyzed' columns in the 'catalogs' table
def update_catalog_collected(session: Session, catalog_id: int, collected: bool):
    stmt = update(Catalog).where(Catalog.catalog_id == catalog_id).values(collected=collected)
    session.execute(stmt)
    session.commit()

def update_catalog_analyzed(session: Session, catalog_id: int, analyzed: bool):
    stmt = update(Catalog).where(Catalog.catalog_id == catalog_id).values(analyzed=analyzed)
    session.execute(stmt)
    session.commit()

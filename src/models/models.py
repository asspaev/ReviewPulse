from sqlalchemy import create_engine, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# Base class for SQLAlchemy ORM models
class Base(DeclarativeBase):
    pass

# Model for the 'catalogs' table
class Catalog(Base):
    __tablename__ = 'catalogs'
    
    catalog_id: Mapped[int] = mapped_column(primary_key=True, unique=True)
    catalog_link: Mapped[str] = mapped_column(nullable=False)
    collected: Mapped[bool] = mapped_column(nullable=False)
    analyzed: Mapped[bool] = mapped_column(nullable=False)
    
    # Relationship with 'products' table
    products: Mapped[list['Product']] = relationship("Product", back_populates="catalog")


# Model for the 'products' table
class Product(Base):
    __tablename__ = 'products'
    
    product_article: Mapped[int] = mapped_column(primary_key=True)
    catalog_id: Mapped[int] = mapped_column(ForeignKey('catalogs.catalog_id'), nullable=False)
    name: Mapped[str] = mapped_column(nullable=False)
    rating: Mapped[float] = mapped_column(nullable=False)
    count_reviews: Mapped[int] = mapped_column(nullable=False)
    
    # Relationship with 'catalogs' and 'reviews' table
    catalog: Mapped['Catalog'] = relationship("Catalog", back_populates="products")
    reviews: Mapped[list['Review']] = relationship("Review", back_populates="product")


# Model for the 'reviews' table
class Review(Base):
    __tablename__ = 'reviews'
    
    review_id: Mapped[int] = mapped_column(primary_key=True, unique=True)
    product_article: Mapped[int] = mapped_column(ForeignKey('products.product_article'), nullable=False)
    rating: Mapped[int] = mapped_column(nullable=False)
    text_all: Mapped[str] = mapped_column(nullable=True)
    text_plus: Mapped[str] = mapped_column(nullable=True)
    text_minus: Mapped[str] = mapped_column(nullable=True)
    text_comment: Mapped[str] = mapped_column(nullable=True)
    
    # Relationship with 'products' table
    product: Mapped['Product'] = relationship("Product", back_populates="reviews")


# Model for the 'analysis' table
class Analysis(Base):
    __tablename__ = 'analysis'
    
    word: Mapped[str] = mapped_column(primary_key=True)
    frequency: Mapped[float] = mapped_column(nullable=False)
    df_index: Mapped[str] = mapped_column(nullable=False)
    column: Mapped[str] = mapped_column(nullable=False)


# Create engines for the main and copy databases
main_engine = create_engine('sqlite:///base.db')
copy_engine = create_engine('sqlite:///analysis_1.db')

# Create all tables for the main database
Base.metadata.create_all(main_engine)

# Create all tables for a copy database (analysis_X.db)
Base.metadata.create_all(copy_engine)

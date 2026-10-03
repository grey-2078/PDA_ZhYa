from sqlalchemy import String, Integer, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
engine = create_engine('sqlite:///books.db')
class Base(DeclarativeBase):
    pass
class Book(Base):
    __tablename__ = 'books'
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    author: Mapped[str] = mapped_column(String, nullable=False)
    year: Mapped[int | None] = mapped_column(Integer)
    edition_count: Mapped[int | None] = mapped_column(Integer)
    book_key: Mapped[str] = mapped_column(String, nullable=False, unique=True)
Base.metadata.create_all(engine)
def save_book(title, author, year, edition_count, book_key):
    with Session(engine) as session:
        existing_book = session.query(Book).filter_by(book_key=book_key).first()
        if existing_book is None:
            book = Book(
                title=title,
                author=author,
                year=year,
                edition_count=edition_count,
                book_key=book_key
            )
            session.add(book)
            session.commit()


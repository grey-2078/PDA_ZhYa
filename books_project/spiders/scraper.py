import scrapy

from books_project.models import save_book


class BooksSpider(scrapy.Spider):
    name = "books"
    start_urls = [f"https://openlibrary.org/search.json?q=book&limit=100&page={page}" for page in range(1, 16)]

    def parse(self, response):
        data = response.json()
        for book in data["docs"]:
            title = book.get("title")
            authors = book.get("author_name", [])
            author = authors[0] if len(authors) > 0 else "Unknown"
            year = book.get("first_publish_year")
            edition_count = book.get("edition_count")
            book_key = book.get("key")
            if title and book_key:
                save_book(title, author, year, edition_count, book_key)

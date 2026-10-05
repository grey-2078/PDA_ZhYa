import scrapy

from books_project.models import save_book


class BooksSpider(scrapy.Spider):
    name = "books"
    start_urls = [
        "https://openlibrary.org/search.json?q=book&limit=100&page=1",
        "https://openlibrary.org/search.json?q=book&limit=100&page=2",
        "https://openlibrary.org/search.json?q=book&limit=100&page=3",
        "https://openlibrary.org/search.json?q=book&limit=100&page=4",
        "https://openlibrary.org/search.json?q=book&limit=100&page=5",
        "https://openlibrary.org/search.json?q=book&limit=100&page=6",
        "https://openlibrary.org/search.json?q=book&limit=100&page=7",
        "https://openlibrary.org/search.json?q=book&limit=100&page=8",
        "https://openlibrary.org/search.json?q=book&limit=100&page=9",
        "https://openlibrary.org/search.json?q=book&limit=100&page=10",
        "https://openlibrary.org/search.json?q=book&limit=100&page=11",
        "https://openlibrary.org/search.json?q=book&limit=100&page=12",
        "https://openlibrary.org/search.json?q=book&limit=100&page=13",
        "https://openlibrary.org/search.json?q=book&limit=100&page=14",
        "https://openlibrary.org/search.json?q=book&limit=100&page=15",
    ]

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

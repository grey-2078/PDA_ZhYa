import pandas as pd
from sqlalchemy.orm import Session
from books_project.models import engine, Book


def main():

    with Session(engine) as session:
        query = session.query(Book)
        df = pd.read_sql(query.statement, session.bind)

        if df.empty:
            print("база данных пуста")
            return

        # уникальные ключи (книги) от авторов
        top_authors = (
            df.groupby('author')['book_key']
            .count()
            .reset_index()
            .rename(columns={'book_key': 'books_count'})
            .sort_values(by='books_count', ascending=False)
            .head(10)
        )
        print("\nТОП-10 авторов по количеству книг:\n", top_authors.to_string(index=False))

        # авторы, у которых самые популярные книги
        author_editions = (
            df.groupby('author')['edition_count']
            .sum()
            .reset_index()
            .sort_values(by='edition_count', ascending=False)
            .head(5)
        )
        print("\n ТОП-5 самых популярных авторов:\n", author_editions.to_string(index=False))

        # группируем по векам и фильтруем некорректные данные
        df_clean_years = df[df['year'].notna() & (df['year'] > 0) & (df['year'] <= 2026)].copy()

        df_clean_years['century'] = (df_clean_years['year'] - 1) // 100 + 1

        century_stats = df_clean_years.groupby('century').agg(
            books_count=('book_key', 'count'),
            avg_editions=('edition_count', 'mean')
        ).reset_index()

        century_stats['century'] = century_stats['century'].astype(int).astype(str) + "-й век"
        print("\nраспределение книг и средних переизданий по векам:\n", century_stats.to_string(index=False))

        # делим на редкость
        bins = [-1, 1, 5, 20, float('inf')]
        labels = ['1 издание', '2-5 изданий', '6-20 изданий', '20+ изданий']

        df['popularity_segment'] = pd.cut(df['edition_count'].fillna(0), bins=bins, labels=labels)

        segment_analysis = df.groupby('popularity_segment', observed=False).agg(
            count=('book_key', 'count'),
            avg_year=('year', 'mean')
        ).reset_index()


        segment_analysis['avg_year'] = segment_analysis['avg_year'].round(0)
        print("\nкниги по популярности:\n", segment_analysis.to_string(index=False))

        # авторы, у которых самая большая разница между их самой старой и самой новой книге
        author_longevity = df_clean_years.groupby('author').agg(
            first_book=('year', 'min'),
            last_book=('year', 'max'),
            total_books=('book_key', 'count')
        ).reset_index()

        author_longevity['career_span_years'] = author_longevity['last_book'] - author_longevity['first_book']

        # фильтруем тех, у кого больше 1 книги и сортируем по длительности карьеры
        long_career_authors = (
            author_longevity[author_longevity['total_books'] > 1]
            .sort_values(by='career_span_years', ascending=False)
            .head(5)
        )
        print("\nтоп авторов по продолжительности издательской карьеры:\n",
              long_career_authors.to_string(index=False))

        # авторы с 80% всех переизданий
        author_abc = df.groupby('author')['edition_count'].sum().reset_index()
        author_abc = author_abc.sort_values(by='edition_count', ascending=False).reset_index(drop=True)

        # кумулятивная сумма переизданий
        author_abc['cum_editions'] = author_abc['edition_count'].cumsum()
        total_editions = author_abc['edition_count'].sum()

        if total_editions > 0:
            author_abc['cum_percentage'] = (author_abc['cum_editions'] / total_editions) * 100
        else:
            author_abc['cum_percentage'] = 0

        author_abc['abc_class'] = pd.cut(
            author_abc['cum_percentage'], bins=[0, 80, 95, 100.1], labels=['A', 'B', 'C'], include_lowest=True
        )

        abc_summary = author_abc.groupby('abc_class', observed=False).agg(
            authors_count=('author', 'count'),
            total_editions=('edition_count', 'sum')
        ).reset_index()

        print("\nу кого из авторов основной объем переизданий:\n", abc_summary.to_string(index=False))


if __name__ == '__main__':
    main()

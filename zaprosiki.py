import pandas as pd
from sqlalchemy.orm import Session
from books_project.models import engine, Book
from sqlalchemy import func, desc

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

        # анализ сегментов: количество книг, % от общего числа и сумма всех переизданий
        segment_analysis = df.groupby('popularity_segment', observed=False).agg(
            books_count=('book_key', 'count'),
            total_editions=('edition_count', 'sum')
        ).reset_index()

        # добавляем долю от общего количества книг
        total_books = len(df)
        segment_analysis['share_pct'] = (segment_analysis['books_count'] / total_books * 100).round(1)

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

        # группируем суммарные переиздания по авторам
        author_stats = df.groupby('author')['edition_count'].sum().reset_index()

        # порог для попадания в ТОП-10%
        top_10_threshold = author_stats['edition_count'].quantile(0.90)

        # делим авторов на 2 группы
        author_stats['author_group'] = author_stats['edition_count'].apply(
            lambda x: 'ТОП-10% авторов' if x >= top_10_threshold else 'Остальные 90%'
        )

        # сводный анализ
        concentration_summary = author_stats.groupby('author_group').agg(
            authors_count=('author', 'count'),
            total_editions=('edition_count', 'sum')
        ).reset_index()

        # доли в процентах
        total_editions = concentration_summary['total_editions'].sum()
        total_authors = concentration_summary['authors_count'].sum()

        concentration_summary['authors_share_%'] = (concentration_summary['authors_count'] / total_authors * 100).round(
            1)
        concentration_summary['editions_share_%'] = (
                    concentration_summary['total_editions'] / total_editions * 100).round(1)

        print("\nконцентрация переизданий ТОП-10% авторов vs Остальные:\n",
              concentration_summary.to_string(index=False))



        # самые популярные классические книги
        old_popular_books = (
            session.query(
                Book.title,
                Book.author,
                Book.year,
                Book.edition_count
            )
            .filter(Book.year.isnot(None), Book.year > 0)
            .order_by(desc(Book.edition_count), Book.year.asc())
            .limit(5)
            .all()
        )

        df_old_popular = pd.DataFrame(old_popular_books, columns=['название', 'автор', 'год', 'переизданий'])
        print("\nТОП-5 самых популярной классики (ранний год + много изданий):\n", df_old_popular.to_string(index=False))


        # авторы с наибольшим числом книг, у которых 1 издание
        prolific_single_edition_authors = (
            session.query(
                Book.author,
                func.count(Book.book_key).label('single_edition_books')
            )
            .filter(Book.edition_count == 1)
            .group_by(Book.author)
            .order_by(desc('single_edition_books'))
            .limit(5)
            .all()
        )

        df_single_edition = pd.DataFrame(prolific_single_edition_authors, columns=['автор', 'книг с 1 изданием'])
        print("\nавторы с наибольшим числом книг, у которых 1 издание:\n", df_single_edition.to_string(index=False))


        # среднее количество переизданий на одну книгу у ТОП-5 авторов
        author_avg_editions = (
            session.query(
                Book.author,
                func.count(Book.book_key).label('total_books'),
                func.round(func.avg(Book.edition_count), 2).label('avg_editions_per_book')
            )
            .group_by(Book.author)
            .order_by(desc('total_books'))
            .limit(5)
            .all()
        )

        df_avg_editions = pd.DataFrame(author_avg_editions, columns=['автор', 'всего книг', 'среднее изданий/книгу'])
        print("\nсреднее количество переизданий на одну книгу у ТОП-5 авторов:\n", df_avg_editions.to_string(index=False))


if __name__ == '__main__':
    main()

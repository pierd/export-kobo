#!/usr/bin/env python3

import argparse
import datetime
import os
import sqlite3
import sys


DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]


class Item:
    """A highlight or annotation from a book."""

    ANNOTATION = "annotation"
    BOOKMARK = "bookmark"
    HIGHLIGHT = "highlight"

    def __init__(self, values, book):
        self.volumeid = values[0]
        self.text = values[1].strip().rstrip() if values[1] else None
        self.annotation = values[2]
        self.datecreated = values[3] if values[3] is not None else "1970-01-01T00:00:00.000"
        self.chapter_progress = values[5] if values[5] is not None else 0
        self.chapter = values[7]
        self.start_offset = values[10] if values[10] is not None else 0
        self.volume_index = values[11] if values[11] is not None else 0
        self.color = values[12] if values[12] is not None else 0
        self.kind = self.BOOKMARK

        if self.text and self.annotation:
            self.kind = self.ANNOTATION
        elif self.text:
            self.kind = self.HIGHLIGHT

    def markdown(self, debug=False, colors=None):
        """Output markdown for highlights and annotations."""
        debug_info = ""
        if debug:
            debug_info = (
                f"\n>\n> **Debug:** kind={self.kind}, volume_index={self.volume_index}, "
                f"start_offset={self.start_offset}, chapter_progress={self.chapter_progress}, "
                f"datecreated={self.datecreated}, color={self.color}"
            )
        color_prefix = ""
        if colors and 0 <= self.color < len(colors):
            color_prefix = f"{colors[self.color]} "
        if self.kind == self.ANNOTATION:
            return f"> {color_prefix}{self.text}{debug_info}\n\n- {self.annotation}\n\n"
        elif self.kind == self.HIGHLIGHT:
            return f"> {color_prefix}{self.text}{debug_info}\n\n"
        return ""


class Book:
    """A book with annotations/highlights."""

    def __init__(self, values):
        self.volumeid = values[0]
        self.title = values[1]
        self.author = values[2]
        self.itemscount = values[3]

    def to_markdown(self):
        return f"---\ntitle: {self.title}\nauthor: {self.author}\n---\n# \"{self.title}\" by {self.author}\n"


class ExportKobo:
    """Export annotations and highlights from a Kobo SQLite file."""

    QUERY_DB_VERSION = "SELECT version FROM DbVersion;"

    QUERY_ITEMS_V175 = """
        SELECT b.VolumeID, b.Text, b.Annotation, b.DateCreated, b.DateModified, b.ChapterProgress,
               c.BookTitle, c.Title as Chapter, c.Attribution as Author, b.BookmarkID, b.StartOffset,
               c.VolumeIndex, b.Color
        FROM Bookmark b INNER JOIN content c ON b.ContentID = c.ContentID 
        GROUP BY b.BookmarkID ORDER BY c.VolumeIndex ASC, b.StartOffset ASC;
    """

    QUERY_ITEMS_V174 = """
        SELECT b.VolumeID, b.Text, b.Annotation, b.DateCreated, b.DateModified, b.ChapterProgress,
               c.BookTitle, c.Title as Chapter, c.Attribution as Author, b.BookmarkID, b.StartOffset,
               c.VolumeIndex, b.Color
        FROM Bookmark b LEFT JOIN content c ON b.ContentID = c.ContentID 
        GROUP BY b.BookmarkID ORDER BY c.VolumeIndex ASC, b.StartOffset ASC;
    """

    QUERY_BOOKS = """
        SELECT DISTINCT b.VolumeID, c.Title, c.Attribution as Author,
               (SELECT COUNT(*) FROM Bookmark b2 WHERE b2.VolumeID = b.VolumeID) AS Items
        FROM Bookmark b INNER JOIN content c ON b.VolumeID = c.ContentID
        ORDER BY c.Title;
    """

    def __init__(self, db_path):
        self.db_path = db_path
        self.db_version = self._get_db_version()
        self.books = self._load_books()

    def _query(self, query):
        """Run a query on the SQLite database."""
        if not os.path.exists(self.db_path):
            print(f"Error: Cannot read {self.db_path}", file=sys.stderr)
            sys.exit(1)
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(query)
            data = cursor.fetchall()
            cursor.close()
            conn.close()
            return data
        except Exception as e:
            print(f"Error reading database: {e}", file=sys.stderr)
            sys.exit(1)

    def _get_db_version(self):
        result = self._query(self.QUERY_DB_VERSION)
        return int(result[0][0])

    def _load_books(self):
        return [Book(row) for row in self._query(self.QUERY_BOOKS)]

    def list_books(self):
        """Print list of books with their IDs."""
        print(f"{'ID':<4} {'AUTHOR':<30} TITLE")
        print("-" * 80)
        for i, book in enumerate(self.books, start=1):
            author = (book.author or "Unknown")[:30]
            print(f"{i:<4} {author:<30} {book.title}")

    def export_markdown(self, book_id, debug=False, colors=None):
        """Export highlights/annotations for a book as markdown."""
        if book_id < 1 or book_id > len(self.books):
            print(f"Error: bookid must be between 1 and {len(self.books)}", file=sys.stderr)
            sys.exit(1)

        book = self.books[book_id - 1]
        dict_books = {b.volumeid: b for b in self.books}

        query = self.QUERY_ITEMS_V175 if self.db_version == 175 else self.QUERY_ITEMS_V174
        items = [Item(row, dict_books.get(row[0])) for row in self._query(query)]
        items = [i for i in items if i.volumeid == book.volumeid]

        # Group items by chapter
        chapters = {}
        for item in items:
            if item.chapter not in chapters:
                chapters[item.chapter] = []
            chapters[item.chapter].append(item)

        # Sort chapters by the minimum volume_index of their items (chapter order in the book)
        sorted_chapters = sorted(chapters.keys(), key=lambda ch: min(i.volume_index for i in chapters[ch]))

        # Sort items within each chapter by start_offset (position within chapter)
        for chapter in chapters:
            chapters[chapter].sort(key=lambda i: i.start_offset)

        output = book.to_markdown()
        for chapter in sorted_chapters:
            output += f"\n### {chapter}\n\n"
            for item in chapters[chapter]:
                output += item.markdown(debug=debug, colors=colors)

        print(output)


def main():
    parser = argparse.ArgumentParser(description="Export annotations and highlights from a Kobo SQLite file.")
    parser.add_argument("db", help="Path to KoboReader.sqlite file")
    parser.add_argument("--list", action="store_true", help="List books with annotations/highlights")
    parser.add_argument("--bookid", type=int, help="Export markdown for book with given ID")
    parser.add_argument("--debug", action="store_true", help="Include debug info in markdown output")
    parser.add_argument("--colors", type=str, help="Comma-separated labels for colors 0-3 (e.g. 'yellow,red,blue,green')")
    parser.add_argument("--no-colors", action="store_true", help="Don't show color marks")

    args = parser.parse_args()

    if not args.list and args.bookid is None:
        parser.print_help()
        sys.exit(1)

    colors = ["🟡", "🔴", "🔵", "🟢"]  # Default emoji colors
    if getattr(args, 'no_colors', False):
        colors = None
    elif args.colors:
        colors = [c.strip() for c in args.colors.split(',')]

    kobo = ExportKobo(args.db)

    if args.list:
        kobo.list_books()
    elif args.bookid:
        kobo.export_markdown(args.bookid, debug=args.debug, colors=colors)


if __name__ == "__main__":
    main()

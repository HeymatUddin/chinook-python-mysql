"""Shared connection and display helpers for the supplied Chinook MySQL schema."""
import getpass
import mysql.connector


def connect():
    return mysql.connector.connect(
        host="localhost", port=3306, user="root",
        password=getpass.getpass("MySQL password: "), database="Chinook"
    )


def print_table(headers, rows):
    rows = [["" if value is None else str(value) for value in row] for row in rows]
    widths = [max([len(h)] + [len(r[i]) for r in rows]) for i, h in enumerate(headers)]
    def line(row):
        return " | ".join(value.ljust(widths[i]) for i, value in enumerate(row))
    print(line(headers))
    print("-+-".join("-" * w for w in widths))
    for row in rows:
        print(line(row))


def next_id(cursor, table, column):
    # Only fixed, developer-defined identifiers are accepted; values use parameters.
    allowed = {("Genre", "GenreId"), ("Playlist", "PlaylistId"), ("Track", "TrackId")}
    if (table, column) not in allowed:
        raise ValueError("Unsupported identifier")
    cursor.execute(f"SELECT COALESCE(MAX(`{column}`), 0) + 1 FROM `{table}`")
    return cursor.fetchone()[0]

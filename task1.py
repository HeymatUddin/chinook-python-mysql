"""Task 1: track display, genre insertion, Jazz update and playlist deletion."""
from decimal import Decimal
import mysql.connector
from db import connect, print_table, next_id


def main():
    connection = connect()
    cursor = connection.cursor()
    try:
        print("Connected to Chinook successfully!")
        
        print("\n=== Q1: FIRST 20 TRACKS ===")
        cursor.execute("SELECT TrackId, Name, Composer, UnitPrice FROM Track ORDER BY TrackId LIMIT %s", (20,))
        print_table(["TrackId", "Name", "Composer", "UnitPrice"], cursor.fetchall())
        

        print("\n=== Q2: INSERT LO-FI GENRE ===")
        cursor.execute("SELECT GenreId, Name FROM Genre WHERE Name = %s", ("Lo-fi",))
        genre = cursor.fetchone()
        if genre is None:
            genre_id = next_id(cursor, "Genre", "GenreId")
            cursor.execute("INSERT INTO Genre (GenreId, Name) VALUES (%s, %s)", (genre_id, "Lo-fi"))
            connection.commit()
            print("Lo-fi inserted successfully.")
        else:
            print("Lo-fi already exists; no duplicate inserted.")
        cursor.execute("SELECT GenreId, Name FROM Genre WHERE Name = %s", ("Lo-fi",))
        print_table(["GenreId", "Name"], cursor.fetchall())
        

        print("\n=== Q3: INCREASE ALL JAZZ PRICES BY 10% ===")
        cursor.execute("SELECT TrackId, UnitPrice FROM Track WHERE GenreId IN (SELECT GenreId FROM Genre WHERE Name = %s)", ("Jazz",))
        old_prices = dict(cursor.fetchall())
        cursor.execute("UPDATE Track SET UnitPrice = ROUND(UnitPrice * %s, 2) WHERE GenreId IN (SELECT GenreId FROM Genre WHERE Name = %s)", (Decimal("1.10"), "Jazz"))
        count = cursor.rowcount
        connection.commit()
        print(f"Jazz tracks updated: {count}")
        cursor.execute("SELECT t.TrackId, t.Name, t.UnitPrice FROM Track t JOIN Genre g ON t.GenreId = g.GenreId WHERE g.Name = %s ORDER BY t.TrackId", ("Jazz",))
        jazz = cursor.fetchall()
        print_table(["TrackId", "Name", "Before", "Updated UnitPrice"],
                    [(i, name, old_prices.get(i, "not updated this run"), price) for i, name, price in jazz])
        

        print("\n=== Q4: CREATE AND DELETE TEST PLAYLIST ===")
        cursor.execute("SELECT TrackId FROM Track ORDER BY TrackId LIMIT %s", (3,))
        track_ids = [row[0] for row in cursor.fetchall()]
        if len(track_ids) != 3:
            raise ValueError("At least three tracks are required.")
        playlist_id = next_id(cursor, "Playlist", "PlaylistId")
        cursor.execute("INSERT INTO Playlist (PlaylistId, Name) VALUES (%s, %s)", (playlist_id, "Test Playlist"))
        cursor.executemany("INSERT INTO PlaylistTrack (PlaylistId, TrackId) VALUES (%s, %s)", [(playlist_id, i) for i in track_ids])
        # Read back the parent and its three child rows before deleting them.
        cursor.execute("SELECT p.PlaylistId, p.Name, t.TrackId, t.Name FROM Playlist p JOIN PlaylistTrack pt ON p.PlaylistId = pt.PlaylistId JOIN Track t ON pt.TrackId = t.TrackId WHERE p.PlaylistId = %s ORDER BY t.TrackId", (playlist_id,))
        print_table(["PlaylistId", "Playlist", "TrackId", "Track"], cursor.fetchall())
        cursor.execute("DELETE FROM PlaylistTrack WHERE PlaylistId = %s", (playlist_id,))
        print(f"PlaylistTrack rows deleted first: {cursor.rowcount}")
        cursor.execute("DELETE FROM Playlist WHERE PlaylistId = %s", (playlist_id,))
        print(f"Playlist rows deleted second: {cursor.rowcount}")
        connection.commit()
        cursor.execute("SELECT COUNT(*) FROM Playlist WHERE PlaylistId = %s", (playlist_id,))
        print(f"Playlist rows remaining: {cursor.fetchone()[0]}")
        cursor.execute("SELECT COUNT(*) FROM PlaylistTrack WHERE PlaylistId = %s", (playlist_id,))
        print(f"PlaylistTrack rows remaining: {cursor.fetchone()[0]}")
        
    except (mysql.connector.Error, ValueError):
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    main()

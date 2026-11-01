"""Task 2: use historical invoice-line prices for genre and country revenue."""
from pathlib import Path
from decimal import Decimal
import pandas as pd
from db import connect


def main():
    connection = connect()
    cursor = connection.cursor()
    try:
        frames = {}
        # These are fixed SQL statements; no user values are interpolated.
        queries = {
            "Invoice": "SELECT * FROM Invoice",
            "InvoiceLine": "SELECT * FROM InvoiceLine",
            "Track": "SELECT * FROM Track",
            "Genre": "SELECT * FROM Genre"
        }
        for name, query in queries.items():
            cursor.execute(query)
            frames[name] = pd.DataFrame(cursor.fetchall(), columns=cursor.column_names)
            print(f"{name} loaded: {len(frames[name])}")
    finally:
        cursor.close()
        connection.close()

    # Keep InvoiceLine.UnitPrice: Track.UnitPrice can change after the sale.
    tracks = frames["Track"][["TrackId", "Name", "GenreId"]].rename(columns={"Name": "TrackName"})
    genres = frames["Genre"][["GenreId", "Name"]].rename(columns={"Name": "GenreName"})
    merged = frames["InvoiceLine"].merge(
        frames["Invoice"][["InvoiceId", "BillingCountry"]],
        on="InvoiceId", how="left", validate="many_to_one", indicator=True)
    if (merged["_merge"] != "both").any():
        raise ValueError("InvoiceLine contains an unknown invoice.")
    merged = merged.drop(columns="_merge").merge(tracks, on="TrackId", how="left", validate="many_to_one", indicator=True)
    if (merged["_merge"] != "both").any():
        raise ValueError("InvoiceLine contains an unknown track.")
    merged = merged.drop(columns="_merge").merge(genres, on="GenreId", how="left", validate="many_to_one")
    merged["GenreName"] = merged["GenreName"].fillna("Unknown genre")
    merged["BillingCountry"] = merged["BillingCountry"].fillna("Unknown country")
    if merged[["UnitPrice", "Quantity"]].isna().any().any():
        raise ValueError("Missing price or quantity.")
    merged["LineTotal"] = [price * int(qty) for price, qty in zip(merged["UnitPrice"], merged["Quantity"])]
    print("\n=== MERGED DATA: FIRST 10 ROWS ===")
    print(merged[["InvoiceId", "TrackId", "TrackName", "GenreName", "BillingCountry", "UnitPrice", "Quantity", "LineTotal"]].head(10).to_string(index=False))

    genre_revenue = merged.groupby(["GenreId", "GenreName"], as_index=False, dropna=False).agg(TotalRevenue=("LineTotal", "sum"))
    # Include genres that have no sales, with zero revenue.
    genre_revenue = genres.merge(genre_revenue, on=["GenreId", "GenreName"], how="left", validate="one_to_one")
    genre_revenue["TotalRevenue"] = genre_revenue["TotalRevenue"].fillna(Decimal("0.00"))
    country_revenue = merged.groupby("BillingCountry", as_index=False).agg(TotalRevenue=("LineTotal", "sum"))
    for label, data, tie, filename in [
        ("GENRE", genre_revenue, "GenreId", "top_5_genres.csv"),
        ("COUNTRY", country_revenue, "BillingCountry", "top_5_countries.csv")
    ]:
        data = data.sort_values(["TotalRevenue", tie], ascending=[False, True])
        print(f"\n=== REVENUE BY {label} ===")
        print(data.to_string(index=False))
        top = data.head(5).copy()
        print(f"\n=== TOP 5 {label} RESULTS ===")
        print(top.to_string(index=False))
        top["TotalRevenue"] = top["TotalRevenue"].map(lambda value: f"{value:.2f}")
        path = Path(__file__).resolve().parent / filename
        top.to_csv(path, index=False, encoding="utf-8-sig")
        print(f"Saved: {path}")
    total = sum(merged["LineTotal"], Decimal("0.00"))
    assert sum(genre_revenue["TotalRevenue"]) == total
    assert sum(country_revenue["TotalRevenue"]) == total
    print(f"\nRevenue reconciled across lines, genres and countries: {total:.2f}")


if __name__ == "__main__":
    main()

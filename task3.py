"""Task 3: hashed login, track CRUD, partial search and customer invoice CSV."""
import csv
import hashlib
import hmac
from decimal import Decimal, InvalidOperation
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import mysql.connector
from db import connect, next_id


class ChinookApp:
    def __init__(self, root, connection):
        self.root, self.connection = root, connection
        root.title("Chinook Employee Login")
        root.geometry("420x300")
        root.protocol("WM_DELETE_WINDOW", self.close)
        frame = ttk.Frame(root, padding=25)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Employee Login", font=("Segoe UI", 16, "bold")).pack(pady=10)
        ttk.Label(frame, text="EmployeeId").pack(anchor="w")
        self.employee = ttk.Entry(frame)
        self.employee.pack(fill="x", pady=5)
        ttk.Label(frame, text="Password").pack(anchor="w")
        self.password = ttk.Entry(frame, show="*")
        self.password.pack(fill="x", pady=5)
        ttk.Button(frame, text="Login", command=self.login).pack(fill="x", pady=10)
        root.bind("<Return>", lambda event: self.login())

    def query(self, sql, params=()):
        # Every cursor is closed; autocommit ensures fresh reads after changes.
        cursor = self.connection.cursor()
        try:
            cursor.execute(sql, params)
            return cursor.fetchall()
        finally:
            cursor.close()

    def login(self):
        try:
            employee_id = int(self.employee.get().strip())
            entered = hashlib.sha256(self.password.get().encode("utf-8")).hexdigest()
            rows = self.query("SELECT FirstName, LastName, Password FROM Employee WHERE EmployeeId = %s", (employee_id,))
            if not rows or not rows[0][2] or not hmac.compare_digest(rows[0][2], entered):
                messagebox.showerror("Login Failed", "Incorrect EmployeeId or password.")
                self.password.delete(0, tk.END)
                return
            self.name = f"{rows[0][0]} {rows[0][1]}"
            messagebox.showinfo("Login Successful", f"Welcome, {self.name}!")
            self.build_tracks()
        except (ValueError, mysql.connector.Error) as error:
            messagebox.showerror("Login Error", str(error))

    def build_tracks(self):
        self.root.unbind("<Return>")
        for widget in self.root.winfo_children():
            widget.destroy()
        self.root.title("Chinook Tracks")
        self.root.geometry("1150x650")
        ttk.Label(self.root, text=f"Welcome, {self.name}", font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=15, pady=10)
        toolbar = ttk.Frame(self.root)
        toolbar.pack(fill="x", padx=15, pady=5)
        for title, callback in [("Add Track", self.add_track), ("Update Price", self.update_price), ("Delete Track", self.delete_track), ("Export Customer Invoices", self.export_invoices)]:
            ttk.Button(toolbar, text=title, command=callback).pack(side="left", padx=(0, 10))
        search_frame = ttk.Frame(self.root)
        search_frame.pack(fill="x", padx=15, pady=5)
        ttk.Label(search_frame, text="Track name or genre:").pack(side="left")
        self.search = ttk.Entry(search_frame, width=45)
        self.search.pack(side="left", padx=10)
        self.search.bind("<Return>", lambda event: self.load_tracks())
        ttk.Button(search_frame, text="Search", command=self.load_tracks).pack(side="left")
        ttk.Button(search_frame, text="Show All", command=self.clear_search).pack(side="left", padx=10)
        frame = ttk.Frame(self.root)
        frame.pack(fill="both", expand=True, padx=15, pady=10)
        columns = ("TrackId", "Name", "Album Title", "Genre", "UnitPrice")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings", selectmode="browse")
        for column, width in zip(columns, [75, 340, 300, 150, 100]):
            self.tree.heading(column, text=column)
            self.tree.column(column, width=width, anchor="w")
        self.tree.column("UnitPrice", anchor="e")
        vertical = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        horizontal = ttk.Scrollbar(frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        self.count = ttk.Label(self.root)
        self.count.pack(anchor="w", padx=15, pady=5)
        self.load_tracks()

    def clear_search(self):
        self.search.delete(0, tk.END)
        self.load_tracks()

    def load_tracks(self):
        try:
            text = self.search.get().strip()
            # Escape LIKE wildcards so user text is a literal partial match.
            pattern = "%" + text.replace("!", "!!").replace("%", "!%").replace("_", "!_") + "%"
            rows = self.query("SELECT t.TrackId, t.Name, a.Title, g.Name, t.UnitPrice FROM Track t LEFT JOIN Album a ON t.AlbumId = a.AlbumId LEFT JOIN Genre g ON t.GenreId = g.GenreId WHERE t.Name LIKE %s ESCAPE '!' OR g.Name LIKE %s ESCAPE '!' ORDER BY t.TrackId", (pattern, pattern))
            self.tree.delete(*self.tree.get_children())
            for i, name, album, genre, price in rows:
                self.tree.insert("", "end", values=(i, name, album or "", genre or "", f"{price:.2f}"))
            self.count.config(text=f"Displayed tracks: {len(rows)}")
        except mysql.connector.Error as error:
            messagebox.showerror("Database Error", str(error))

    def selected(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Select Track", "Select a track first.")
            return None
        return self.tree.item(selection[0], "values")

    @staticmethod
    def price(value):
        price = Decimal(value.strip())
        if not price.is_finite() or price < 0 or price > Decimal("99999999.99") or price != price.quantize(Decimal("0.01")):
            raise ValueError("Enter a non-negative price with at most two decimal places.")
        return price

    def add_track(self):
        window = tk.Toplevel(self.root)
        window.title("Add Track")
        window.transient(self.root)
        window.grab_set()
        form = ttk.Frame(window, padding=20)
        form.pack(fill="both", expand=True)
        entries = {}
        fields = ["Name", "AlbumId (optional)", "MediaTypeId", "GenreId (optional)", "Composer (optional)", "Milliseconds", "Bytes (optional)", "UnitPrice"]
        for row, label in enumerate(fields):
            ttk.Label(form, text=label).grid(row=row, column=0, sticky="w", pady=5)
            entries[label] = ttk.Entry(form, width=40)
            entries[label].grid(row=row, column=1, pady=5)
        entries["MediaTypeId"].insert(0, "1")
        entries["Milliseconds"].insert(0, "180000")
        entries["UnitPrice"].insert(0, "0.99")
        def save():
            cursor = self.connection.cursor()
            try:
                values = {key: entry.get().strip() for key, entry in entries.items()}
                name = values["Name"]
                composer = values["Composer (optional)"] or None
                if not name or len(name) > 200 or (composer and len(composer) > 220):
                    raise ValueError("Name must have 1–200 characters; composer at most 220.")
                album = int(values["AlbumId (optional)"]) if values["AlbumId (optional)"] else None
                genre = int(values["GenreId (optional)"]) if values["GenreId (optional)"] else None
                media = int(values["MediaTypeId"])
                milliseconds = int(values["Milliseconds"])
                byte_count = int(values["Bytes (optional)"]) if values["Bytes (optional)"] else None
                if not 0 < milliseconds <= 2147483647 or (byte_count is not None and not 0 <= byte_count <= 2147483647):
                    raise ValueError("Use a positive duration and a non-negative Bytes value within INT range.")
                for sql, identifier in [("SELECT AlbumId FROM Album WHERE AlbumId = %s", album), ("SELECT GenreId FROM Genre WHERE GenreId = %s", genre), ("SELECT MediaTypeId FROM MediaType WHERE MediaTypeId = %s", media)]:
                    if identifier is not None:
                        cursor.execute(sql, (identifier,))
                        if cursor.fetchone() is None:
                            raise ValueError("AlbumId, GenreId or MediaTypeId does not exist.")
                track_id = next_id(cursor, "Track", "TrackId")
                cursor.execute("INSERT INTO Track (TrackId, Name, AlbumId, MediaTypeId, GenreId, Composer, Milliseconds, Bytes, UnitPrice) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)", (track_id, name, album, media, genre, composer, milliseconds, byte_count, self.price(values["UnitPrice"])))
                messagebox.showinfo("Added", f"Track added: {track_id} — {name}", parent=window)
                window.destroy()
                self.clear_search()
            except (ValueError, InvalidOperation, mysql.connector.Error) as error:
                messagebox.showerror("Add Error", str(error), parent=window)
            finally:
                cursor.close()
        ttk.Button(form, text="Save Track", command=save).grid(row=len(fields), column=1, pady=15)

    def update_price(self):
        row = self.selected()
        if row is None:
            return
        entered = simpledialog.askstring("Update Price", f"New price for {row[1]}", initialvalue=row[4], parent=self.root)
        if entered is None:
            return
        cursor = self.connection.cursor()
        try:
            price = self.price(entered)
            cursor.execute("UPDATE Track SET UnitPrice = %s WHERE TrackId = %s", (price, int(row[0])))
            messagebox.showinfo("Updated", f"{row[1]}\nBefore: {row[4]}\nAfter: {price:.2f}")
            self.load_tracks()
        except (ValueError, InvalidOperation, mysql.connector.Error) as error:
            messagebox.showerror("Update Error", str(error))
        finally:
            cursor.close()

    def delete_track(self):
        row = self.selected()
        if row is None:
            return
        cursor = self.connection.cursor()
        try:
            # Child playlist memberships and track deletion are one transaction.
            self.connection.start_transaction()
            cursor.execute("SELECT TrackId FROM Track WHERE TrackId = %s FOR UPDATE", (int(row[0]),))
            if cursor.fetchone() is None:
                raise ValueError("Track no longer exists.")
            cursor.execute("SELECT COUNT(*) FROM InvoiceLine WHERE TrackId = %s", (int(row[0]),))
            if cursor.fetchone()[0]:
                self.connection.rollback()
                messagebox.showwarning("Delete Blocked", "This track has already been sold and appears in InvoiceLine. It cannot be deleted.")
                return
            if not messagebox.askyesno("Confirm Delete", f"Delete {row[1]} and its playlist memberships?"):
                self.connection.rollback()
                return
            cursor.execute("DELETE FROM PlaylistTrack WHERE TrackId = %s", (int(row[0]),))
            cursor.execute("DELETE FROM Track WHERE TrackId = %s", (int(row[0]),))
            self.connection.commit()
            messagebox.showinfo("Deleted", f"{row[1]} deleted successfully.")
            self.load_tracks()
        except (ValueError, mysql.connector.Error) as error:
            self.connection.rollback()
            messagebox.showerror("Delete Error", str(error))
        finally:
            cursor.close()

    def export_invoices(self):
        try:
            customers = self.query("SELECT CustomerId, FirstName, LastName FROM Customer ORDER BY CustomerId")
            window = tk.Toplevel(self.root)
            window.title("Select Customer")
            window.transient(self.root)
            window.grab_set()
            ttk.Label(window, text="Customer:").pack(padx=20, pady=10)
            choices = [f"{i} — {first} {last}" for i, first, last in customers]
            combo = ttk.Combobox(window, values=choices, state="readonly", width=45)
            combo.pack(padx=20, pady=10)
            if choices:
                combo.current(0)
            def export():
                if combo.current() < 0:
                    return
                customer_id = customers[combo.current()][0]
                path = filedialog.asksaveasfilename(parent=window, defaultextension=".csv", initialfile=f"customer_{customer_id}_invoices.csv", filetypes=[("CSV", "*.csv")])
                if not path:
                    return
                cursor = self.connection.cursor()
                try:
                    cursor.execute("SELECT * FROM Invoice WHERE CustomerId = %s ORDER BY InvoiceId", (customer_id,))
                    headers = cursor.column_names
                    rows = cursor.fetchall()
                    with open(path, "w", newline="", encoding="utf-8-sig") as file:
                        writer = csv.writer(file)
                        writer.writerow(headers)
                        writer.writerows(rows)
                    messagebox.showinfo("Export Successful", f"Customer {customer_id}: {len(rows)} invoices exported.\n{path}", parent=window)
                    window.destroy()
                except (OSError, mysql.connector.Error) as error:
                    messagebox.showerror("Export Error", str(error), parent=window)
                finally:
                    cursor.close()
            ttk.Button(window, text="Export CSV", command=export).pack(pady=15)
        except mysql.connector.Error as error:
            messagebox.showerror("Database Error", str(error))

    def close(self):
        self.connection.close()
        self.root.destroy()


if __name__ == "__main__":
    connection = connect()
    connection.autocommit = True
    root = tk.Tk()
    ChinookApp(root, connection)
    root.mainloop()

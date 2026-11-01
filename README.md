# Chinook Python and MySQL Application

An academic project combining SQL database operations, sales analysis with pandas, and a Tkinter desktop application using the Chinook sample database.

## Technologies

Python, MySQL, mysql-connector-python, pandas and Tkinter.

## Features

### Database Operations — task1.py

- Display the first 20 tracks.
- Insert a Lo-fi genre without creating a duplicate.
- Increase Jazz track prices by 10%.
- Create and delete a test playlist, removing child records before the parent.

### Sales Analysis — task2.py

- Load invoice, invoice-line, track and genre data into pandas.
- Validate relationships during data merges.
- Calculate revenue using historical invoice-line prices and quantities.
- Summarise revenue by genre and billing country.
- Export the top five genres and countries to CSV.
- Reconcile grouped revenue against the invoice-line total.

### Desktop Application — task3.py

- Employee login using demonstration password hashes.
- Browse and search tracks by name or genre.
- Add tracks and update prices with input validation.
- Block deletion of tracks referenced by historical sales.
- Delete eligible tracks and playlist memberships in one transaction.
- Export a selected customer's invoices to CSV.

## Files

| File | Purpose |
|---|---|
| db.py | Database connection and shared helpers |
| setup_login.py | Prepare demonstration employee logins |
| task1.py | SQL operations |
| task2.py | Sales analysis and CSV exports |
| task3.py | Tkinter desktop application |
| requirements.txt | Python dependencies |

## Requirements

- Python with Tkinter available
- A running MySQL server
- A compatible Chinook MySQL sample database

The database import script is not included in this repository. Import the assignment-compatible Chinook schema separately before running the application.

The code expects tables such as Employee, Track, Genre, Album, Playlist, PlaylistTrack, Invoice, InvoiceLine and Customer, with their original column names.

## Setup

1. Import the compatible Chinook database into MySQL.
2. Check the connection settings in db.py:
   localhost, port 3306, user root and database Chinook.
3. Install dependencies:

```bash
python -m pip install -r requirements.txt
```

The MySQL password is requested interactively using getpass; it is not stored in the source code.

## Run

Prepare demonstration logins:

```bash
python setup_login.py
```

Run database operations:

```bash
python task1.py
```

Run sales analysis:

```bash
python task2.py
```

Launch the desktop application:

```bash
python task3.py
```

Each script requests the MySQL password separately. The desktop application then asks for an employee login.

## Important Behaviour and Limitations

- Run only against a disposable local copy of the sample database.
- task1.py modifies data. Each execution increases the current Jazz prices by another 10%.
- setup_login.py alters the Employee table and creates predictable demonstration passwords for accounts without a password.
- Login uses unsalted SHA-256 for the academic demonstration. This is not suitable for production password storage.
- The setup script prints demonstration credentials and hashes; do not use real credentials.
- New IDs use MAX(ID) + 1, intended for this single-user lab rather than concurrent applications.
- The connection defaults to MySQL root for the local assessment setup. A deployed application would need a dedicated account with restricted permissions.
- This is an academic desktop project, not a production service.

## Data

Chinook is a sample music-store dataset. Generated CSV files and the assessment report are excluded from version control.
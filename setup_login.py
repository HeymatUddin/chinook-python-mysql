"""Run once: add Employee.Password and store SHA-256 hashes for demo accounts."""
import hashlib
from db import connect


def main():
    connection = connect()
    cursor = connection.cursor()
    try:
        cursor.execute("SHOW COLUMNS FROM Employee LIKE %s", ("Password",))
        if cursor.fetchone() is None:
            cursor.execute("ALTER TABLE Employee ADD COLUMN Password VARCHAR(64) NULL")
        cursor.execute("SELECT EmployeeId, FirstName, LastName FROM Employee WHERE Password IS NULL OR Password = %s ORDER BY EmployeeId", ("",))
        employees = cursor.fetchall()
        for employee_id, first, last in employees:
            demo_password = f"Demo{employee_id}Pass"
            digest = hashlib.sha256(demo_password.encode("utf-8")).hexdigest()
            cursor.execute("UPDATE Employee SET Password = %s WHERE EmployeeId = %s", (digest, employee_id))
            print(f"EmployeeId {employee_id}: {first} {last} | demo login password: {demo_password}")
        connection.commit()
        print("Only SHA-256 hashes were stored. Existing passwords were not overwritten.")
        cursor.execute("SELECT EmployeeId, FirstName, LastName, Password FROM Employee ORDER BY EmployeeId")
        for row in cursor.fetchall():
            print(row)
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    main()

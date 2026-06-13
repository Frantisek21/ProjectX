import sqlite3
from collections import defaultdict

DB_PATH = "expenses.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS people (
                id   INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            );

            CREATE TABLE IF NOT EXISTS groups (
                id   INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS group_members (
                group_id  INTEGER REFERENCES groups(id),
                person_id INTEGER REFERENCES people(id),
                PRIMARY KEY (group_id, person_id)
            );

            CREATE TABLE IF NOT EXISTS expenses (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id    INTEGER REFERENCES groups(id),
                description TEXT NOT NULL,
                amount      REAL NOT NULL,
                paid_by_id  INTEGER REFERENCES people(id),
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS expense_splits (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                expense_id INTEGER REFERENCES expenses(id),
                person_id  INTEGER REFERENCES people(id),
                amount     REAL NOT NULL
            );
        """)


# --- People ---

def add_person(name: str) -> int:
    with get_conn() as conn:
        cur = conn.execute("INSERT INTO people (name) VALUES (?)", (name,))
        return cur.lastrowid


def get_all_people():
    with get_conn() as conn:
        return conn.execute("SELECT * FROM people ORDER BY name").fetchall()


# --- Groups ---

def create_group(name: str, member_ids: list[int]) -> int:
    with get_conn() as conn:
        cur = conn.execute("INSERT INTO groups (name) VALUES (?)", (name,))
        group_id = cur.lastrowid
        conn.executemany(
            "INSERT INTO group_members (group_id, person_id) VALUES (?, ?)",
            [(group_id, pid) for pid in member_ids],
        )
        return group_id


def get_all_groups():
    with get_conn() as conn:
        return conn.execute("SELECT * FROM groups ORDER BY name").fetchall()


def get_group(group_id: int):
    with get_conn() as conn:
        return conn.execute("SELECT * FROM groups WHERE id = ?", (group_id,)).fetchone()


def get_group_members(group_id: int):
    with get_conn() as conn:
        return conn.execute("""
            SELECT p.* FROM people p
            JOIN group_members gm ON gm.person_id = p.id
            WHERE gm.group_id = ?
            ORDER BY p.name
        """, (group_id,)).fetchall()


# --- Expenses ---

def add_expense(group_id: int, description: str, amount: float, paid_by_id: int, splits: dict[int, float]):
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO expenses (group_id, description, amount, paid_by_id) VALUES (?, ?, ?, ?)",
            (group_id, description, amount, paid_by_id),
        )
        expense_id = cur.lastrowid
        conn.executemany(
            "INSERT INTO expense_splits (expense_id, person_id, amount) VALUES (?, ?, ?)",
            [(expense_id, pid, amt) for pid, amt in splits.items()],
        )


def get_group_expenses(group_id: int):
    with get_conn() as conn:
        return conn.execute("""
            SELECT e.*, p.name AS paid_by_name
            FROM expenses e
            JOIN people p ON p.id = e.paid_by_id
            WHERE e.group_id = ?
            ORDER BY e.created_at DESC
        """, (group_id,)).fetchall()


# --- Balances ---

def get_balances(group_id: int):
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT e.paid_by_id, es.person_id, es.amount
            FROM expense_splits es
            JOIN expenses e ON e.id = es.expense_id
            WHERE e.group_id = ?
        """, (group_id,)).fetchall()

    # owes[debtor_id][creditor_id] += amount
    owes = defaultdict(lambda: defaultdict(float))
    for row in rows:
        creditor_id = row["paid_by_id"]
        debtor_id = row["person_id"]
        if debtor_id != creditor_id:
            owes[debtor_id][creditor_id] += row["amount"]

    # Resolve names
    people_map = {p["id"]: p["name"] for p in get_all_people()}

    results = []
    seen = set()
    for debtor_id, creditors in owes.items():
        for creditor_id, amount in creditors.items():
            pair = tuple(sorted([debtor_id, creditor_id]))
            if pair in seen:
                continue
            seen.add(pair)
            net = owes[debtor_id][creditor_id] - owes[creditor_id][debtor_id]
            if net > 0.005:
                results.append({
                    "debtor": people_map[debtor_id],
                    "creditor": people_map[creditor_id],
                    "amount": round(net, 2),
                })
            elif net < -0.005:
                results.append({
                    "debtor": people_map[creditor_id],
                    "creditor": people_map[debtor_id],
                    "amount": round(-net, 2),
                })

    return sorted(results, key=lambda x: x["amount"], reverse=True)

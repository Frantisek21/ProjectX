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
                id    INTEGER PRIMARY KEY AUTOINCREMENT,
                name  TEXT NOT NULL UNIQUE,
                color TEXT DEFAULT '#4A90D9',
                pfp   TEXT
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
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS settings (
                key   TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
        """)
        # Safe migrations for databases created before these columns existed
        for migration in [
            "ALTER TABLE people ADD COLUMN color TEXT DEFAULT '#4A90D9'",
            "ALTER TABLE people ADD COLUMN pfp TEXT",
            "ALTER TABLE expenses ADD COLUMN settled INTEGER DEFAULT 0",
        ]:
            try:
                conn.execute(migration)
            except Exception:
                pass


# --- People ---

def add_person(name: str) -> int:
    with get_conn() as conn:
        cur = conn.execute("INSERT INTO people (name) VALUES (?)", (name,))
        return cur.lastrowid


def get_all_people():
    with get_conn() as conn:
        return conn.execute("SELECT * FROM people ORDER BY name").fetchall()


def get_all_people_map() -> dict:
    with get_conn() as conn:
        rows = conn.execute("SELECT id, name, color, pfp FROM people").fetchall()
    return {r["id"]: dict(r) for r in rows}


def get_person(person_id: int):
    with get_conn() as conn:
        return conn.execute("SELECT * FROM people WHERE id = ?", (person_id,)).fetchone()


def get_setting(key: str, default: str = "") -> str:
    with get_conn() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else default


def set_setting(key: str, value: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )


def update_person_profile(person_id: int, color: str, pfp_b64: str | None):
    with get_conn() as conn:
        if pfp_b64 is not None:
            conn.execute(
                "UPDATE people SET color = ?, pfp = ? WHERE id = ?",
                (color, pfp_b64, person_id),
            )
        else:
            conn.execute(
                "UPDATE people SET color = ? WHERE id = ?",
                (color, person_id),
            )


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


def set_expense_settled(expense_id: int, settled: bool):
    with get_conn() as conn:
        conn.execute("UPDATE expenses SET settled = ? WHERE id = ?", (1 if settled else 0, expense_id))


# --- Balances ---

def get_balances(group_id: int):
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT e.paid_by_id, es.person_id, es.amount
            FROM expense_splits es
            JOIN expenses e ON e.id = es.expense_id
            WHERE e.group_id = ? AND e.settled = 0
        """, (group_id,)).fetchall()

    # owes[debtor_id][creditor_id] += amount
    owes = defaultdict(lambda: defaultdict(float))
    for row in rows:
        creditor_id = row["paid_by_id"]
        debtor_id = row["person_id"]
        if debtor_id != creditor_id:
            owes[debtor_id][creditor_id] += row["amount"]

    all_people = get_all_people_map()

    results = []
    seen = set()
    for debtor_id, creditors in list(owes.items()):
        for creditor_id, amount in list(creditors.items()):
            pair = tuple(sorted([debtor_id, creditor_id]))
            if pair in seen:
                continue
            seen.add(pair)
            net = owes[debtor_id][creditor_id] - owes[creditor_id].get(debtor_id, 0)
            if net > 0.005:
                results.append({
                    "debtor_id": debtor_id,
                    "debtor": all_people[debtor_id]["name"],
                    "creditor_id": creditor_id,
                    "creditor": all_people[creditor_id]["name"],
                    "amount": round(net, 2),
                })
            elif net < -0.005:
                results.append({
                    "debtor_id": creditor_id,
                    "debtor": all_people[creditor_id]["name"],
                    "creditor_id": debtor_id,
                    "creditor": all_people[debtor_id]["name"],
                    "amount": round(-net, 2),
                })

    return sorted(results, key=lambda x: x["amount"], reverse=True)

# SplitEasy

A lightweight expense-splitting web app built with Python and Streamlit. Track shared expenses across groups and instantly see who owes what to whom — no accounts, no fluff, just clear numbers.

---

## Features

- Create groups and add people to them
- Log expenses with a description, total amount, and who paid
- Split any expense equally among selected group members
- View a clean balance summary showing net debts between people

## Tech Stack

- **Python** — core language
- **Streamlit** — UI and app framework
- **SQLite** — local database, zero configuration required

## Getting Started

**Prerequisites:** Python 3.10+

```bash
# Clone the repository
git clone https://github.com/Frantisek21/ProjectX.git
cd ProjectX

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`.

## Usage

1. Go to **Groups** — add the people involved and create a group
2. Go to **Add Expense** — select a group, enter what was spent, who paid, and who splits it
3. Go to **Balances** — see the simplified settlement summary for any group

## Project Structure

```
ProjectX/
├── app.py               # Home page
├── db.py                # Database setup and all queries
├── pages/
│   ├── 1_Groups.py      # Manage people and groups
│   ├── 2_Add_Expense.py # Log new expenses
│   └── 3_Balances.py    # View who owes whom
└── requirements.txt
```

## Roadmap

- Custom split amounts (not just equal splits)
- Expense categories and filtering
- Settlement history (mark debts as paid)
- Export balances to CSV

## License

MIT

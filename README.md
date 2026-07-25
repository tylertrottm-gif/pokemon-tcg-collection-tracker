# Pokémon TCG Collection Tracker

A Streamlit app for tracking a personal Pokémon Trading Card Game collection by expansion set. It retrieves current card and set metadata from the Pokémon TCG API and stores owned-card records in Supabase.

## MVP features

- Browse every expansion set returned by the Pokémon TCG API
- Filter by series, expansion set, ownership status, rarity, card name, or card number
- Add and remove cards from the collection
- Track duplicate quantities
- Review owned cards in a dedicated collection page
- Export the collection to CSV
- Compare completion across expansion sets
- Optional owner-PIN screen
- Session-only demo mode when Supabase is not connected

## Project structure

```text
pokemon_tcg_collection_tracker/
├── app.py
├── pages/
│   ├── 1_Set_Browser.py
│   ├── 2_My_Collection.py
│   └── 3_Set_Progress.py
├── src/
│   ├── database.py
│   ├── pokemon_api.py
│   └── ui.py
├── sql/
│   └── setup.sql
├── .streamlit/
│   ├── config.toml
│   └── secrets.toml.example
├── requirements.txt
├── .gitignore
└── README.md
```

## 1. Create a Pokémon TCG API key

1. Open the Pokémon TCG Developer Portal.
2. Create a free account and API key.
3. Keep the key private. The app sends it through the `X-Api-Key` request header.

The API can run without a key, but the unauthenticated rate limit is much lower.

## 2. Create the Supabase database

1. Create a new Supabase project.
2. Open **SQL Editor**.
3. Paste and run the contents of `sql/setup.sql`.
4. Open **Project Settings → API**.
5. Copy the project URL and anon/public key.

The current MVP is designed for one private collection. It does not yet provide separate user accounts.

## 3. Configure local secrets

Create `.streamlit/secrets.toml` by copying `.streamlit/secrets.toml.example`:

```toml
[pokemon_tcg]
api_key = "your-pokemon-tcg-api-key"

[supabase]
url = "https://your-project.supabase.co"
key = "your-supabase-anon-key"

[app]
owner_pin = "choose-a-private-pin"
```

Do not commit `.streamlit/secrets.toml`. It is already included in `.gitignore`.

The owner PIN is optional. Set it to an empty string to disable the PIN screen.

## 4. Run locally

From the project folder:

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

macOS/Linux:

```bash
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Without Supabase secrets, the app automatically starts in demo mode. Demo changes disappear when the browser session ends.

## 5. Push to GitHub

Create a new GitHub repository and run:

```bash
git init
git add .
git commit -m "Build Pokémon TCG collection tracker MVP"
git branch -M main
git remote add origin YOUR_GITHUB_REPOSITORY_URL
git push -u origin main
```

Before pushing, confirm that `.streamlit/secrets.toml` does not appear in the staged files.

## 6. Deploy on Streamlit Community Cloud

1. Open Streamlit Community Cloud.
2. Select **Create app**.
3. Choose the GitHub repository and `main` branch.
4. Set the entry point to `app.py`.
5. Open **Advanced settings → Secrets**.
6. Paste the contents of your local `.streamlit/secrets.toml`.
7. Deploy the app.

## Data model

The `collection_items` table stores one row per unique card:

| Column | Purpose |
|---|---|
| `card_id` | Pokémon TCG API card ID and primary key |
| `card_name` | Card name |
| `set_id` | API expansion-set ID |
| `set_name` | Expansion-set name |
| `card_number` | Printed number within the set |
| `rarity` | API rarity value |
| `image_small` | Card image URL |
| `quantity` | Number of copies owned |
| `date_added` | Original date added |
| `updated_at` | Last quantity update |

The API remains the source of truth for the full card catalog. Supabase stores only owned cards and a small metadata snapshot.

## Recommended next enhancements

- Separate normal, holo, and reverse-holo variants
- Card condition and grading
- Purchase price and current market value
- Wish list and trade list
- User accounts for multiple collectors
- Mobile card scanning
- Collection import from CSV

## Important note

This is a fan-made personal collection tool and is not affiliated with or endorsed by Nintendo, Creatures Inc., The Pokémon Company, or The Pokémon Company International.

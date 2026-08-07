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

## Potential next enhancements

- Separate normal, holo, and reverse-holo variants
- Card condition and grading
- Purchase price and current market value
- Wish list and trade list
- User accounts for multiple collectors
- Mobile card scanning
- Collection import from CSV

## Important note

This is a fan-made personal collection tool and is not affiliated with or endorsed by Nintendo, Creatures Inc., The Pokémon Company, or The Pokémon Company International.

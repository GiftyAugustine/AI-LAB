import sqlite3
import csv
import os
import time
import traceback

DB_FILE = "recipes.db"
CSV_FILE = "recipes.csv"
BATCH_SIZE = 5000  # how many rows to insert per batch

def create_database():
    """Create an FTS5 full-text search database for fast recipe lookups."""
    try:
        if os.path.exists(DB_FILE):
            print(f"⚠️ Existing database '{DB_FILE}' found. Deleting old file...")
            os.remove(DB_FILE)

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # Create virtual FTS5 table
        cursor.execute("""
        CREATE VIRTUAL TABLE recipes USING fts5(
            name,
            ingredients,
            instructions,
            content='',
            tokenize = 'porter'
        )
        """)
        conn.commit()
        conn.close()
        print("✅ Created FTS5 database structure successfully!\n")

    except Exception as e:
        print("❌ Error creating database:", e)
        traceback.print_exc()

def load_recipes():
    """Load recipes from CSV into SQLite FTS5 database with batch inserts."""
    if not os.path.exists(CSV_FILE):
        print(f"❌ CSV file '{CSV_FILE}' not found!")
        return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    start_time = time.time()
    total_inserted = 0
    batch = []

    print(f"📦 Starting import from '{CSV_FILE}'...")
    print(f"⚙️ Using batch size: {BATCH_SIZE} rows per commit\n")

    try:
        with open(CSV_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader, start=1):
                try:
                    name = row.get("recipe_name", "").strip()
                    ingredients = row.get("description", "").strip()
                    instructions = row.get("description", "").strip()

                    if not name or not ingredients:
                        continue  # skip empty rows

                    batch.append((name, ingredients, instructions))

                    if len(batch) >= BATCH_SIZE:
                        cursor.executemany(
                            "INSERT INTO recipes (name, ingredients, instructions) VALUES (?, ?, ?)",
                            batch
                        )
                        conn.commit()
                        total_inserted += len(batch)
                        print(f"✅ Inserted {total_inserted:,} rows so far...")
                        batch.clear()

                except Exception as row_error:
                    print(f"⚠️ Error processing row {i}: {row_error}")
                    traceback.print_exc()
                    continue

            # Insert any remaining rows
            if batch:
                cursor.executemany(
                    "INSERT INTO recipes (name, ingredients, instructions) VALUES (?, ?, ?)",
                    batch
                )
                conn.commit()
                total_inserted += len(batch)

    except Exception as e:
        print("❌ Error during CSV import:", e)
        traceback.print_exc()
    finally:
        conn.close()

    duration = time.time() - start_time
    print("\n🎯 Import complete!")
    print(f"📊 Total rows inserted: {total_inserted:,}")
    print(f"⏱️ Time taken: {duration:.2f} seconds")
    print(f"📁 Database file: {DB_FILE}")

def verify_database():
    """Verify that data was inserted successfully."""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM recipes")
        total = cursor.fetchone()[0]
        conn.close()
        print(f"\n🔍 Verification complete: {total:,} total recipes in database.")
    except Exception as e:
        print("❌ Verification failed:", e)
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Starting Recipe Database Loader...")
    create_database()
    load_recipes()
    verify_database()
    print("\n✅ All steps finished successfully!")

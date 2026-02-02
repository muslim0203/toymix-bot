"""
Database migration script to add category_id column to toys table
"""
import sqlite3
import os

def migrate_database(db_path="toymix.db"):
    """Add category_id column to toys table if it doesn't exist"""
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found. It will be created on first run.")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if category_id column exists
        cursor.execute("PRAGMA table_info(toys)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'category_id' not in columns:
            print("Adding category_id column to toys table...")
            cursor.execute("ALTER TABLE toys ADD COLUMN category_id INTEGER")
            conn.commit()
            print("✅ category_id column added successfully!")
        else:
            print("✅ category_id column already exists.")
        
        # Check if categories table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='categories'")
        if not cursor.fetchone():
            print("Creating categories table...")
            cursor.execute("""
                CREATE TABLE categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(100) NOT NULL UNIQUE,
                    is_active BOOLEAN NOT NULL DEFAULT 1,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            print("✅ categories table created successfully!")
        else:
            print("✅ categories table already exists.")
        
        # Check if daily_ads_log table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='daily_ads_log'")
        if not cursor.fetchone():
            print("Creating daily_ads_log table...")
            cursor.execute("""
                CREATE TABLE daily_ads_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    toy_id INTEGER NOT NULL,
                    category_id INTEGER,
                    posted_date VARCHAR(10) NOT NULL,
                    posted_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (toy_id) REFERENCES toys(id),
                    FOREIGN KEY (category_id) REFERENCES categories(id)
                )
            """)
            conn.commit()
            print("✅ daily_ads_log table created successfully!")
        else:
            print("✅ daily_ads_log table already exists.")
        
        # Check if order_contacts table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='order_contacts'")
        if not cursor.fetchone():
            print("Creating order_contacts table...")
            cursor.execute("""
                CREATE TABLE order_contacts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    contact_value VARCHAR(255) NOT NULL UNIQUE,
                    is_active BOOLEAN NOT NULL DEFAULT 1,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            print("✅ order_contacts table created successfully!")
        else:
            print("✅ order_contacts table already exists.")
        
        # Check if sales_logs table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sales_logs'")
        if not cursor.fetchone():
            print("Creating sales_logs table...")
            cursor.execute("""
                CREATE TABLE sales_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    toy_id INTEGER NOT NULL,
                    toy_name VARCHAR(255) NOT NULL,
                    category_id INTEGER,
                    category_name VARCHAR(100),
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (toy_id) REFERENCES toys(id),
                    FOREIGN KEY (category_id) REFERENCES categories(id)
                )
            """)
            # Create indexes for performance
            cursor.execute("CREATE INDEX idx_sales_logs_user_id ON sales_logs(user_id)")
            cursor.execute("CREATE INDEX idx_sales_logs_toy_id ON sales_logs(toy_id)")
            cursor.execute("CREATE INDEX idx_sales_logs_category_id ON sales_logs(category_id)")
            cursor.execute("CREATE INDEX idx_sales_logs_created_at ON sales_logs(created_at)")
            conn.commit()
            print("✅ sales_logs table created successfully!")
        else:
            print("✅ sales_logs table already exists.")
        
        # Check if bestseller_categories table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='bestseller_categories'")
        if not cursor.fetchone():
            print("Creating bestseller_categories table...")
            cursor.execute("""
                CREATE TABLE bestseller_categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category_id INTEGER NOT NULL,
                    category_name VARCHAR(100) NOT NULL,
                    source VARCHAR(10) NOT NULL,
                    period VARCHAR(10) NOT NULL,
                    rank INTEGER NOT NULL,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN NOT NULL DEFAULT 1,
                    FOREIGN KEY (category_id) REFERENCES categories(id)
                )
            """)
            # Create indexes
            cursor.execute("CREATE INDEX idx_bestseller_category_id ON bestseller_categories(category_id)")
            cursor.execute("CREATE INDEX idx_bestseller_is_active ON bestseller_categories(is_active)")
            cursor.execute("CREATE INDEX idx_bestseller_period_rank ON bestseller_categories(period, rank)")
            conn.commit()
            print("✅ bestseller_categories table created successfully!")
        else:
            print("✅ bestseller_categories table already exists.")
        
        # Check if store_locations table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='store_locations'")
        if not cursor.fetchone():
            print("Creating store_locations table...")
            cursor.execute("""
                CREATE TABLE store_locations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(255) NOT NULL,
                    address_text TEXT NOT NULL,
                    latitude VARCHAR(50) NOT NULL,
                    longitude VARCHAR(50) NOT NULL,
                    is_active BOOLEAN NOT NULL DEFAULT 1,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Create indexes
            cursor.execute("CREATE INDEX idx_store_locations_is_active ON store_locations(is_active)")
            conn.commit()
            print("✅ store_locations table created successfully!")
        else:
            print("✅ store_locations table already exists.")
        
        # Check if cart_items table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cart_items'")
        if not cursor.fetchone():
            print("Creating cart_items table...")
            cursor.execute("""
                CREATE TABLE cart_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    toy_id INTEGER NOT NULL,
                    toy_name VARCHAR(255) NOT NULL,
                    price VARCHAR(50) NOT NULL,
                    quantity INTEGER NOT NULL DEFAULT 1,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (toy_id) REFERENCES toys(id)
                )
            """)
            # Create indexes
            cursor.execute("CREATE INDEX idx_cart_items_user_id ON cart_items(user_id)")
            cursor.execute("CREATE INDEX idx_cart_items_toy_id ON cart_items(toy_id)")
            conn.commit()
            print("✅ cart_items table created successfully!")
        else:
            print("✅ cart_items table already exists.")
        
        # Check if favorites table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='favorites'")
        if not cursor.fetchone():
            print("Creating favorites table...")
            cursor.execute("""
                CREATE TABLE favorites (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    toy_id INTEGER NOT NULL,
                    toy_name VARCHAR(255) NOT NULL,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (toy_id) REFERENCES toys(id),
                    UNIQUE(user_id, toy_id)
                )
            """)
            # Create indexes
            cursor.execute("CREATE INDEX idx_favorites_user_id ON favorites(user_id)")
            cursor.execute("CREATE INDEX idx_favorites_toy_id ON favorites(toy_id)")
            conn.commit()
            print("✅ favorites table created successfully!")
        else:
            print("✅ favorites table already exists.")
        
        # Check if toy_media table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='toy_media'")
        if not cursor.fetchone():
            print("Creating toy_media table...")
            cursor.execute("""
                CREATE TABLE toy_media (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    toy_id INTEGER NOT NULL,
                    file_id VARCHAR(255) NOT NULL,
                    media_type VARCHAR(10) NOT NULL,
                    sort_order INTEGER NOT NULL DEFAULT 0,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (toy_id) REFERENCES toys(id) ON DELETE CASCADE
                )
            """)
            # Create indexes
            cursor.execute("CREATE INDEX idx_toy_media_toy_id ON toy_media(toy_id)")
            cursor.execute("CREATE INDEX idx_toy_media_sort_order ON toy_media(toy_id, sort_order)")
            conn.commit()
            print("✅ toy_media table created successfully!")
        else:
            print("✅ toy_media table already exists.")
        
        conn.close()
        print("✅ Database migration completed!")
        
    except Exception as e:
        print(f"❌ Migration error: {e}")
        raise

if __name__ == "__main__":
    # Try to find database file
    possible_paths = [
        "toymix.db",
        os.path.join(os.path.dirname(__file__), "..", "toymix.db"),
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "toymix.db")
    ]
    
    db_path = None
    for path in possible_paths:
        if os.path.exists(path):
            db_path = path
            break
    
    if db_path:
        migrate_database(db_path)
    else:
        print("⚠️  Database file not found. It will be created when bot starts.")
        print("ℹ️  Migration will run automatically on next bot start.")

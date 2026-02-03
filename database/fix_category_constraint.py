"""
Migration script to fix any unique constraints on category_id in toys table
This ensures multiple products can exist in the same category
"""
import sqlite3
import os
import logging

logger = logging.getLogger(__name__)


def check_and_fix_category_constraint(db_path="toymix.db"):
    """
    Check for and remove any unique constraints on category_id in toys table
    
    Args:
        db_path: Path to database file
    """
    if not os.path.exists(db_path):
        logger.info(f"Database file {db_path} not found. It will be created on first run.")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check for unique indexes on category_id
        cursor.execute("""
            SELECT name, sql 
            FROM sqlite_master 
            WHERE type='index' 
            AND tbl_name='toys'
            AND sql LIKE '%category_id%'
        """)
        
        indexes = cursor.fetchall()
        
        for index_name, index_sql in indexes:
            if index_sql and 'UNIQUE' in index_sql.upper():
                logger.warning(f"Found unique index on category_id: {index_name}")
                logger.info(f"Dropping unique index: {index_name}")
                cursor.execute(f"DROP INDEX IF EXISTS {index_name}")
                conn.commit()
                logger.info(f"✅ Dropped unique index: {index_name}")
        
        # Check table structure
        cursor.execute("PRAGMA table_info(toys)")
        columns = cursor.fetchall()
        
        # Verify category_id is NOT unique
        for col in columns:
            col_name, col_type, not_null, default_val, pk, autoinc = col
            if col_name == 'category_id':
                # Check if there's a unique constraint in the table definition
                cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='toys'")
                table_sql = cursor.fetchone()
                if table_sql and table_sql[0]:
                    sql_lower = table_sql[0].lower()
                    # Check for UNIQUE constraint on category_id
                    if 'unique' in sql_lower and 'category_id' in sql_lower:
                        logger.warning("Found UNIQUE constraint on category_id in table definition")
                        logger.warning("This requires manual table recreation. Please backup your data first!")
                    else:
                        logger.info("✅ No unique constraint found on category_id")
        
        # Verify we can have multiple toys with same category_id
        cursor.execute("""
            SELECT category_id, COUNT(*) as count 
            FROM toys 
            WHERE category_id IS NOT NULL 
            GROUP BY category_id 
            HAVING count > 1
        """)
        multiple_toys = cursor.fetchall()
        
        if multiple_toys:
            logger.info(f"✅ Verified: Found {len(multiple_toys)} categories with multiple toys")
            for cat_id, count in multiple_toys:
                logger.info(f"   Category {cat_id}: {count} toys")
        else:
            logger.info("ℹ️  No categories with multiple toys found (this is normal if you just started)")
        
        conn.close()
        logger.info("✅ Category constraint check completed")
        
    except Exception as e:
        logger.error(f"Error checking category constraint: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
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
        check_and_fix_category_constraint(db_path)
    else:
        print("⚠️  Database file not found. It will be created when bot starts.")
        print("ℹ️  The constraint check will run automatically on next bot start.")

#!/usr/bin/env python3
import psycopg2
import os

# Database connection
DATABASE_URL = "postgresql://postgres:H_r4Q7wZs0YS@event-booking-platform-db.cvcceaki0j7j.us-west-2.rds.amazonaws.com:5432/eventdb"

try:
    # Connect to database
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    print("=== DATABASE CONNECTION SUCCESSFUL ===\n")
    
    # Get all tables
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)
    tables = cur.fetchall()
    
    print("=== TABLES IN DATABASE ===")
    for table in tables:
        print(f"- {table[0]}")
    
    print("\n=== TABLE SCHEMAS ===")
    
    # Get schema for each table
    for table in tables:
        table_name = table[0]
        print(f"\n--- {table_name.upper()} TABLE ---")
        
        # Get column information
        cur.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = %s AND table_schema = 'public'
            ORDER BY ordinal_position;
        """, (table_name,))
        
        columns = cur.fetchall()
        for col in columns:
            nullable = "NULL" if col[2] == "YES" else "NOT NULL"
            default = f" DEFAULT {col[3]}" if col[3] else ""
            print(f"  {col[0]}: {col[1]} {nullable}{default}")
        
        # Get row count
        cur.execute(f"SELECT COUNT(*) FROM {table_name};")
        count = cur.fetchone()[0]
        print(f"  Rows: {count}")
        
        # Show sample data if table has data
        if count > 0:
            cur.execute(f"SELECT * FROM {table_name} LIMIT 3;")
            sample_data = cur.fetchall()
            print(f"  Sample data:")
            for row in sample_data:
                print(f"    {row}")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"Error connecting to database: {e}")

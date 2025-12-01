#!/bin/bash
# ===========================================
# AAQIS - Load seed data from compressed SQL
# ===========================================

set -e

echo "AAQIS: Loading seed data..."

# Check if data already exists
COUNT=$(psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "SELECT COUNT(*) FROM unified_data;" 2>/dev/null | tr -d ' ')

if [ "$COUNT" -gt "0" ]; then
    echo "AAQIS: Data already exists ($COUNT records). Skipping seed."
    exit 0
fi

# Load compressed seed data
if [ -f /docker-entrypoint-initdb.d/seed_data.sql.gz ]; then
    echo "AAQIS: Decompressing and loading seed_data.sql.gz..."
    gunzip -c /docker-entrypoint-initdb.d/seed_data.sql.gz | psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"
    
    # Verify
    COUNT=$(psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "SELECT COUNT(*) FROM unified_data;" | tr -d ' ')
    echo "AAQIS: Loaded $COUNT records into unified_data"
else
    echo "AAQIS: WARNING - seed_data.sql.gz not found. Starting with empty database."
fi

echo "AAQIS: Database initialization complete!"

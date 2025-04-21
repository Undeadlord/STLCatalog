import sqlite3
import json
import os
from app_config import DB_FILE, DEFAULT_TAGS

class DatabaseManager:
    """Class to handle all database operations"""
    
    @staticmethod
    def get_tag_usage_count(tag_name):
        """Get the number of files using a specific tag
        
        Args:
            tag_name: Name of the tag
            
        Returns:
            int: Number of files using this tag
        """
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        try:
            # Get tag ID
            cursor.execute("SELECT id FROM tags WHERE name = ?", (tag_name,))
            tag_row = cursor.fetchone()
            
            if not tag_row:
                return 0
                
            tag_id = tag_row[0]
            
            # Count files using this tag
            cursor.execute("SELECT COUNT(*) FROM file_tags WHERE tag_id = ?", (tag_id,))
            count = cursor.fetchone()[0]
            
            return count
            
        except sqlite3.Error as e:
            print(f"Database Error: {e}")
            return 0
        finally:
            conn.close()

    @staticmethod
    def update_tag(old_name, new_name):
        """Update a tag name
        
        Args:
            old_name: Current tag name
            new_name: New tag name
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not old_name or not new_name:
            return False
        
        if old_name == new_name:
            return True  # No change needed
            
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        try:
            # Begin transaction
            conn.execute("BEGIN TRANSACTION")
            
            # Get the ID of the old tag
            cursor.execute("SELECT id FROM tags WHERE name = ?", (old_name,))
            old_tag_row = cursor.fetchone()
            
            if not old_tag_row:
                # Old tag doesn't exist
                conn.rollback()
                return False
            
            old_tag_id = old_tag_row[0]
            
            # Check if new tag already exists
            cursor.execute("SELECT id FROM tags WHERE name = ?", (new_name,))
            existing_tag = cursor.fetchone()
            
            if existing_tag:
                # New tag already exists - we need to move all file associations
                new_tag_id = existing_tag[0]
                
                # Find all files associated with the old tag
                cursor.execute("SELECT file_id FROM file_tags WHERE tag_id = ?", (old_tag_id,))
                file_ids = [row[0] for row in cursor.fetchall()]
                
                # Remove any potential duplicate file-tag associations
                for file_id in file_ids:
                    # Check if this file already has the new tag
                    cursor.execute(
                        "SELECT 1 FROM file_tags WHERE file_id = ? AND tag_id = ?", 
                        (file_id, new_tag_id)
                    )
                    
                    if not cursor.fetchone():
                        # If not, create the association with the new tag
                        cursor.execute(
                            "INSERT INTO file_tags (file_id, tag_id) VALUES (?, ?)",
                            (file_id, new_tag_id)
                        )
                
                # Delete all associations with the old tag
                cursor.execute("DELETE FROM file_tags WHERE tag_id = ?", (old_tag_id,))
                
                # Delete the old tag
                cursor.execute("DELETE FROM tags WHERE id = ?", (old_tag_id,))
                
            else:
                # Create a new tag
                cursor.execute("INSERT INTO tags (name) VALUES (?)", (new_name,))
                
                # Get the ID of the new tag
                cursor.execute("SELECT id FROM tags WHERE name = ?", (new_name,))
                new_tag_row = cursor.fetchone()
                
                if not new_tag_row:
                    # Failed to create new tag
                    conn.rollback()
                    return False
                    
                new_tag_id = new_tag_row[0]
                
                # Find all files associated with the old tag
                cursor.execute("SELECT file_id FROM file_tags WHERE tag_id = ?", (old_tag_id,))
                file_ids = [row[0] for row in cursor.fetchall()]
                
                # Associate all these files with the new tag
                for file_id in file_ids:
                    cursor.execute(
                        "INSERT INTO file_tags (file_id, tag_id) VALUES (?, ?)",
                        (file_id, new_tag_id)
                    )
                
                # Delete all associations with the old tag
                cursor.execute("DELETE FROM file_tags WHERE tag_id = ?", (old_tag_id,))
                
                # Delete the old tag
                cursor.execute("DELETE FROM tags WHERE id = ?", (old_tag_id,))
            
            # Commit the transaction
            conn.commit()
            return True
            
        except sqlite3.Error as e:
            # Roll back any changes if error occurs
            conn.rollback()
            print(f"Database Error: {e}")
            return False
        finally:
            # Close the connection
            conn.close()

    @staticmethod
    def delete_tag(tag_name):
        """Delete a tag and remove it from all files
        
        Args:
            tag_name: Name of the tag to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not tag_name:
            return False
            
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        try:
            # Begin transaction
            conn.execute("BEGIN TRANSACTION")
            
            # Get tag ID
            cursor.execute("SELECT id FROM tags WHERE name = ?", (tag_name,))
            tag_row = cursor.fetchone()
            
            if tag_row:
                tag_id = tag_row[0]
                
                # Delete from file_tags
                cursor.execute("DELETE FROM file_tags WHERE tag_id = ?", (tag_id,))
                
                # Delete the tag
                cursor.execute("DELETE FROM tags WHERE id = ?", (tag_id,))
            
            # Commit the transaction
            conn.commit()
            return True
            
        except sqlite3.Error as e:
            # Roll back any changes if error occurs
            conn.rollback()
            print(f"Database Error: {e}")
            return False
        finally:
            # Close the connection
            conn.close()


    @staticmethod
    def create_database():
        """Create SQLite database if it doesn't exist"""
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Create STL files table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS stl_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT UNIQUE,
            name TEXT,
            date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_multi_part BOOLEAN DEFAULT 0
        )
        ''')
        
        # Create tags table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE
        )
        ''')
        
        # Create relationship table between files and tags
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS file_tags (
            file_id INTEGER,
            tag_id INTEGER,
            PRIMARY KEY (file_id, tag_id),
            FOREIGN KEY (file_id) REFERENCES stl_files (id) ON DELETE CASCADE,
            FOREIGN KEY (tag_id) REFERENCES tags (id) ON DELETE CASCADE
        )
        ''')
        
        # Create related files table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS related_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            main_file_id INTEGER,
            file_path TEXT,
            FOREIGN KEY (main_file_id) REFERENCES stl_files (id) ON DELETE CASCADE
        )
        ''')
        
        conn.commit()
        conn.close()
    
    @staticmethod
    def collect_all_tags():
        """Collect all unique tags from the database"""
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM tags ORDER BY name")
        tags = [row[0] for row in cursor.fetchall()]
        
        # Add default tags if they don't exist
        all_tags = set(tags)
        all_tags.update(DEFAULT_TAGS)
        
        # Insert default tags if they don't exist
        for tag in DEFAULT_TAGS:
            cursor.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (tag,))
        
        conn.commit()
        conn.close()
        
        return sorted(list(all_tags))
    
    @staticmethod
    def add_or_update_file_with_related(file_id, main_file_path, related_files, name, tags):
        """Add new file or update existing file in catalog with related files
        
        Args:
            file_id: ID of file to update (None for new file)
            main_file_path: Path to the main STL file
            related_files: List of paths to related STL files
            name: Display name for catalog entry
            tags: List of tags
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not main_file_path.strip() or not name.strip():
            return False
                
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        try:
            # Begin transaction
            conn.execute("BEGIN TRANSACTION")
            
            # Set is_multi_part flag
            is_multi_part = len(related_files) > 1
            
            if file_id is None:
                # Insert new file
                cursor.execute(
                    "INSERT OR REPLACE INTO stl_files (file_path, name, is_multi_part) VALUES (?, ?, ?)", 
                    (main_file_path, name, is_multi_part)
                )
                
                # Get file_id (either the one just inserted or the existing one)
                cursor.execute("SELECT id FROM stl_files WHERE file_path = ?", (main_file_path,))
                file_id = cursor.fetchone()[0]
            else:
                # Update existing file
                cursor.execute(
                    "UPDATE stl_files SET file_path = ?, name = ?, is_multi_part = ? WHERE id = ?", 
                    (main_file_path, name, is_multi_part, file_id)
                )
            
            # Process tags
            # First, remove existing tag relationships for this file
            cursor.execute("DELETE FROM file_tags WHERE file_id = ?", (file_id,))
            
            # Then add new tags
            for tag in tags:
                # Insert tag if it doesn't exist
                cursor.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (tag,))
                
                # Get tag_id
                cursor.execute("SELECT id FROM tags WHERE name = ?", (tag,))
                tag_id = cursor.fetchone()[0]
                
                # Create relationship between file and tag
                cursor.execute(
                    "INSERT OR IGNORE INTO file_tags (file_id, tag_id) VALUES (?, ?)",
                    (file_id, tag_id)
                )
            
            # Process related files
            # First, remove existing related files
            cursor.execute("DELETE FROM related_files WHERE main_file_id = ?", (file_id,))
            
            # Then add new related files
            for related_path in related_files:
                cursor.execute(
                    "INSERT INTO related_files (main_file_id, file_path) VALUES (?, ?)",
                    (file_id, related_path)
                )
            
            # Commit the transaction
            conn.commit()
            return True
            
        except sqlite3.Error as e:
            # Roll back any changes if error occurs
            conn.rollback()
            print(f"Database Error: {e}")
            return False
        finally:
            # Close the connection
            conn.close()

    @staticmethod
    def get_file_details_with_related(file_id):
        """Get detailed information about a file including related files
        
        Args:
            file_id: ID of the file
            
        Returns:
            dict: File details including related files
        """
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get file details
        cursor.execute('''
        SELECT f.name, f.file_path, f.date_added, f.is_multi_part, GROUP_CONCAT(t.name) as tags
        FROM stl_files f
        LEFT JOIN file_tags ft ON f.id = ft.file_id
        LEFT JOIN tags t ON ft.tag_id = t.id
        WHERE f.id = ?
        GROUP BY f.id
        ''', (file_id,))
        
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return None
        
        details = {
            'name': row['name'],
            'file_path': row['file_path'],
            'date_added': row['date_added'],
            'tags': row['tags'] if row['tags'] else "",
            'is_multi_part': bool(row['is_multi_part']),
            'related_files': []
        }
        
        # Get related files
        cursor.execute('''
        SELECT file_path FROM related_files 
        WHERE main_file_id = ? 
        ORDER BY file_path
        ''', (file_id,))
        
        for related_row in cursor.fetchall():
            details['related_files'].append(related_row['file_path'])
        
        conn.close()
        return details

    @staticmethod
    def add_tag(tag_name):
        """Add a new tag to the database"""
        if not tag_name.strip():
            return False
            
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (tag_name,))
        
        conn.commit()
        conn.close()
        return True
    
    @staticmethod
    def get_filtered_files(search_term=""):
        """Get filtered list of files based on search term"""
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        results = {}
        
        if search_term:
            # Search by name or tags
            cursor.execute('''
            SELECT DISTINCT f.id, f.name, f.file_path
            FROM stl_files f
            LEFT JOIN file_tags ft ON f.id = ft.file_id
            LEFT JOIN tags t ON ft.tag_id = t.id
            WHERE LOWER(f.name) LIKE ? OR LOWER(t.name) LIKE ?
            ORDER BY f.name
            ''', (f'%{search_term.lower()}%', f'%{search_term.lower()}%'))
        else:
            # Get all files
            cursor.execute('''
            SELECT id, name, file_path FROM stl_files ORDER BY name
            ''')
        
        index = 0
        for row in cursor.fetchall():
            file_id = row[0]
            name = row[1]
            file_path = row[2]
            
            results[index] = {
                'id': file_id,
                'name': name,
                'path': file_path
            }
            index += 1
        
        conn.close()
        return results
    
    @staticmethod
    def get_file_details(file_id):
        """Get detailed information about a file"""
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get file details
        cursor.execute('''
        SELECT f.name, f.file_path, f.date_added, GROUP_CONCAT(t.name) as tags
        FROM stl_files f
        LEFT JOIN file_tags ft ON f.id = ft.file_id
        LEFT JOIN tags t ON ft.tag_id = t.id
        WHERE f.id = ?
        GROUP BY f.id
        ''', (file_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'name': row['name'],
                'file_path': row['file_path'],
                'date_added': row['date_added'],
                'tags': row['tags'] if row['tags'] else ""
            }
        return None
    
    @staticmethod
    def add_or_update_file(file_id, file_path, name, tags):
        """Add new file or update existing file in catalog"""
        if not file_path.strip() or not name.strip():
            return False
            
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        try:
            # Begin transaction
            conn.execute("BEGIN TRANSACTION")
            
            if file_id is None:
                # Insert new file
                cursor.execute(
                    "INSERT OR REPLACE INTO stl_files (file_path, name) VALUES (?, ?)", 
                    (file_path, name)
                )
                
                # Get file_id (either the one just inserted or the existing one)
                cursor.execute("SELECT id FROM stl_files WHERE file_path = ?", (file_path,))
                file_id = cursor.fetchone()[0]
            else:
                # Update existing file
                cursor.execute(
                    "UPDATE stl_files SET file_path = ?, name = ? WHERE id = ?", 
                    (file_path, name, file_id)
                )
            
            # Remove existing tag relationships for this file
            cursor.execute("DELETE FROM file_tags WHERE file_id = ?", (file_id,))
            
            # Process tags
            for tag in tags:
                # Insert tag if it doesn't exist
                cursor.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (tag,))
                
                # Get tag_id
                cursor.execute("SELECT id FROM tags WHERE name = ?", (tag,))
                tag_id = cursor.fetchone()[0]
                
                # Create relationship between file and tag
                cursor.execute(
                    "INSERT OR IGNORE INTO file_tags (file_id, tag_id) VALUES (?, ?)",
                    (file_id, tag_id)
                )
            
            # Commit the transaction
            conn.commit()
            return True
            
        except sqlite3.Error as e:
            # Roll back any changes if error occurs
            conn.rollback()
            print(f"Database Error: {e}")
            return False
        finally:
            # Close the connection
            conn.close()
    
    @staticmethod
    def delete_files(file_ids):
        """Delete one or more files from the catalog"""
        if not file_ids:
            return False
            
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        try:
            # Begin transaction
            conn.execute("BEGIN TRANSACTION")
            
            # Delete each file
            for file_id in file_ids:
                # Delete from file_tags first (should cascade, but just to be safe)
                cursor.execute("DELETE FROM file_tags WHERE file_id = ?", (file_id,))
                # Delete the file entry
                cursor.execute("DELETE FROM stl_files WHERE id = ?", (file_id,))
            
            # Commit the transaction
            conn.commit()
            return True
            
        except sqlite3.Error as e:
            # Roll back any changes if error occurs
            conn.rollback()
            print(f"Database Error: {e}")
            return False
        finally:
            # Close the connection
            conn.close()
    
    @staticmethod
    def export_to_json(export_path):
        """Export the database to a JSON file"""
        try:
            conn = sqlite3.connect(DB_FILE)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get all files with their tags
            cursor.execute('''
            SELECT f.id, f.file_path, f.name, GROUP_CONCAT(t.name) as tags
            FROM stl_files f
            LEFT JOIN file_tags ft ON f.id = ft.file_id
            LEFT JOIN tags t ON ft.tag_id = t.id
            GROUP BY f.id
            ''')
            
            export_data = {}
            
            for row in cursor.fetchall():
                file_path = row['file_path']
                tags = row['tags'].split(',') if row['tags'] else []
                export_data[file_path] = {
                    "name": row['name'],
                    "tags": tags
                }
            
            conn.close()
            
            # Write to JSON file
            with open(export_path, 'w') as f:
                json.dump(export_data, f, indent=4)
                
            return True
            
        except Exception as e:
            print(f"Export Error: {e}")
            return False
    
    @staticmethod
    def import_from_json(import_path, replace=False):
        """Import data from a JSON file"""
        try:
            # Load JSON data
            with open(import_path, 'r') as f:
                import_data = json.load(f)
                
            if not import_data:
                return False
                
            # Connect to database
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            try:
                # Begin transaction
                conn.execute("BEGIN TRANSACTION")
                
                # If replace option is selected, clear existing data
                if replace:
                    cursor.execute("DELETE FROM file_tags")
                    cursor.execute("DELETE FROM stl_files")
                    cursor.execute("DELETE FROM tags WHERE name NOT IN (?, ?)", 
                                  (DEFAULT_TAGS[0], DEFAULT_TAGS[1]))
                
                # Import each file
                for file_path, data in import_data.items():
                    # Insert file
                    cursor.execute(
                        "INSERT OR REPLACE INTO stl_files (file_path, name) VALUES (?, ?)",
                        (file_path, data['name'])
                    )
                    
                    # Get file_id
                    cursor.execute("SELECT id FROM stl_files WHERE file_path = ?", (file_path,))
                    file_id = cursor.fetchone()[0]
                    
                    # If merging, remove existing tag relationships for this file
                    if not replace:
                        cursor.execute("DELETE FROM file_tags WHERE file_id = ?", (file_id,))
                    
                    # Process tags
                    for tag in data.get('tags', []):
                        # Insert tag if it doesn't exist
                        cursor.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (tag,))
                        
                        # Get tag_id
                        cursor.execute("SELECT id FROM tags WHERE name = ?", (tag,))
                        tag_id = cursor.fetchone()[0]
                        
                        # Create relationship between file and tag
                        cursor.execute(
                            "INSERT OR IGNORE INTO file_tags (file_id, tag_id) VALUES (?, ?)",
                            (file_id, tag_id)
                        )
                
                # Commit the transaction
                conn.commit()
                return True
                
            except sqlite3.Error as e:
                # Roll back any changes if error occurs
                conn.rollback()
                print(f"Database Error: {e}")
                return False
            finally:
                # Close the connection
                conn.close()
                
        except json.JSONDecodeError:
            print("Import file is not valid JSON.")
            return False
        except Exception as e:
            print(f"Import Error: {e}")
            return False
    
    @staticmethod
    def migrate_json_if_needed():
        """Migrate data from JSON if database is empty and JSON exists"""
        # Check if database is empty
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM stl_files")
        count = cursor.fetchone()[0]
        conn.close()
        
        if count > 0:
            # Database already has data, no need to migrate
            return False
        
        # Check if JSON file exists
        json_file = "stl_catalog.json"
        if not os.path.exists(json_file):
            return False
        
        # Perform import
        return DatabaseManager.import_from_json(json_file, replace=False)
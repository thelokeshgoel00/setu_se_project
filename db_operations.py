#!/usr/bin/env python3
import os
import sys
import argparse
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import engine, Base
from app.db_models import User, PANVerification, ReversePennyDrop, Payment

class DatabaseOperations:
    """
    Utility class for performing various database operations
    """
    def __init__(self):
        """Initialize the database connection"""
        self.engine = engine
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()
        self.inspector = inspect(self.engine)
    
    def close(self):
        """Close the database session"""
        self.session.close()
    
    def reset_table(self, table_name):
        """
        Delete and recreate a specific table
        
        Args:
            table_name (str): Name of the table to reset
        """
        try:
            if table_name not in Base.metadata.tables:
                print(f"Error: Table '{table_name}' does not exist in the metadata")
                return False
                
            print(f"Dropping {table_name} table...")
            self.session.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
            self.session.commit()
            print(f"{table_name} table dropped successfully.")
            
            print(f"Recreating {table_name} table...")
            Base.metadata.tables[table_name].create(bind=self.engine)
            print(f"{table_name} table recreated successfully.")
            
            return True
        except Exception as e:
            print(f"Error resetting table {table_name}: {e}")
            self.session.rollback()
            return False
    
    def delete_rows(self, table_name, conditions=None):
        """
        Delete rows from a table based on conditions
        
        Args:
            table_name (str): Name of the table to delete rows from
            conditions (dict, optional): Dictionary of column-value pairs for WHERE clause
        
        Returns:
            int: Number of rows deleted
        """
        try:
            if table_name not in Base.metadata.tables:
                print(f"Error: Table '{table_name}' does not exist in the metadata")
                return 0
            
            # Build the DELETE query
            query = f"DELETE FROM {table_name}"
            params = {}
            
            # Add WHERE conditions if provided
            if conditions and isinstance(conditions, dict):
                where_clauses = []
                for i, (column, value) in enumerate(conditions.items()):
                    param_name = f"param_{i}"
                    where_clauses.append(f"{column} = :{param_name}")
                    params[param_name] = value
                
                if where_clauses:
                    query += " WHERE " + " AND ".join(where_clauses)
            
            # Execute the query
            result = self.session.execute(text(query), params)
            self.session.commit()
            rows_deleted = result.rowcount
            print(f"Deleted {rows_deleted} rows from {table_name}")
            return rows_deleted
        except Exception as e:
            print(f"Error deleting rows from {table_name}: {e}")
            self.session.rollback()
            return 0
    
    def update_rows(self, table_name, updates, conditions=None):
        """
        Update rows in a table based on conditions
        
        Args:
            table_name (str): Name of the table to update
            updates (dict): Dictionary of column-value pairs to update
            conditions (dict, optional): Dictionary of column-value pairs for WHERE clause
        
        Returns:
            int: Number of rows updated
        """
        try:
            if table_name not in Base.metadata.tables:
                print(f"Error: Table '{table_name}' does not exist in the metadata")
                return 0
            
            if not updates or not isinstance(updates, dict):
                print("Error: updates must be a non-empty dictionary")
                return 0
            
            # Build the UPDATE query
            set_clauses = []
            params = {}
            
            for i, (column, value) in enumerate(updates.items()):
                param_name = f"set_param_{i}"
                set_clauses.append(f"{column} = :{param_name}")
                params[param_name] = value
            
            query = f"UPDATE {table_name} SET " + ", ".join(set_clauses)
            
            # Add WHERE conditions if provided
            if conditions and isinstance(conditions, dict):
                where_clauses = []
                for i, (column, value) in enumerate(conditions.items()):
                    param_name = f"where_param_{i}"
                    where_clauses.append(f"{column} = :{param_name}")
                    params[param_name] = value
                
                if where_clauses:
                    query += " WHERE " + " AND ".join(where_clauses)
            
            # Execute the query
            result = self.session.execute(text(query), params)
            self.session.commit()
            rows_updated = result.rowcount
            print(f"Updated {rows_updated} rows in {table_name}")
            return rows_updated
        except Exception as e:
            print(f"Error updating rows in {table_name}: {e}")
            self.session.rollback()
            return 0
    
    def list_tables(self):
        """List all tables in the database"""
        try:
            tables = self.inspector.get_table_names()
            print("Tables in the database:")
            for table in tables:
                print(f"- {table}")
            return tables
        except Exception as e:
            print(f"Error listing tables: {e}")
            return []
    
    def list_columns(self, table_name):
        """
        List all columns in a table
        
        Args:
            table_name (str): Name of the table
        """
        try:
            if table_name not in self.inspector.get_table_names():
                print(f"Error: Table '{table_name}' does not exist in the database")
                return []
            
            columns = self.inspector.get_columns(table_name)
            print(f"Columns in table '{table_name}':")
            for column in columns:
                print(f"- {column['name']} ({column['type']})")
            return columns
        except Exception as e:
            print(f"Error listing columns for table {table_name}: {e}")
            return []
    
    def count_rows(self, table_name, conditions=None):
        """
        Count rows in a table, optionally with conditions
        
        Args:
            table_name (str): Name of the table
            conditions (dict, optional): Dictionary of column-value pairs for WHERE clause
        
        Returns:
            int: Number of rows
        """
        try:
            if table_name not in self.inspector.get_table_names():
                print(f"Error: Table '{table_name}' does not exist in the database")
                return 0
            
            # Build the COUNT query
            query = f"SELECT COUNT(*) FROM {table_name}"
            params = {}
            
            # Add WHERE conditions if provided
            if conditions and isinstance(conditions, dict):
                where_clauses = []
                for i, (column, value) in enumerate(conditions.items()):
                    param_name = f"param_{i}"
                    where_clauses.append(f"{column} = :{param_name}")
                    params[param_name] = value
                
                if where_clauses:
                    query += " WHERE " + " AND ".join(where_clauses)
            
            # Execute the query
            result = self.session.execute(text(query), params).scalar()
            print(f"Count for {table_name}: {result}")
            return result
        except Exception as e:
            print(f"Error counting rows in {table_name}: {e}")
            return 0

def main():
    """Main function to parse arguments and execute database operations"""
    parser = argparse.ArgumentParser(description="Database Operations Utility")
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Reset table command
    reset_parser = subparsers.add_parser("reset", help="Reset (drop and recreate) a table")
    reset_parser.add_argument("table", help="Name of the table to reset")
    
    # Delete rows command
    delete_parser = subparsers.add_parser("delete", help="Delete rows from a table")
    delete_parser.add_argument("table", help="Name of the table to delete rows from")
    delete_parser.add_argument("--where", nargs="+", help="WHERE conditions in format column=value")
    
    # Update rows command
    update_parser = subparsers.add_parser("update", help="Update rows in a table")
    update_parser.add_argument("table", help="Name of the table to update")
    update_parser.add_argument("--set", nargs="+", required=True, help="SET values in format column=value")
    update_parser.add_argument("--where", nargs="+", help="WHERE conditions in format column=value")
    
    # List tables command
    subparsers.add_parser("list-tables", help="List all tables in the database")
    
    # List columns command
    columns_parser = subparsers.add_parser("list-columns", help="List columns in a table")
    columns_parser.add_argument("table", help="Name of the table")
    
    # Count rows command
    count_parser = subparsers.add_parser("count", help="Count rows in a table")
    count_parser.add_argument("table", help="Name of the table to count rows from")
    count_parser.add_argument("--where", nargs="+", help="WHERE conditions in format column=value")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Initialize database operations
    db_ops = DatabaseOperations()
    
    try:
        if args.command == "reset":
            db_ops.reset_table(args.table)
        
        elif args.command == "delete":
            conditions = {}
            if args.where:
                for condition in args.where:
                    try:
                        column, value = condition.split("=", 1)
                        conditions[column.strip()] = value.strip()
                    except ValueError:
                        print(f"Invalid condition format: {condition}. Use column=value")
            
            db_ops.delete_rows(args.table, conditions)
        
        elif args.command == "update":
            updates = {}
            for update in args.set:
                try:
                    column, value = update.split("=", 1)
                    updates[column.strip()] = value.strip()
                except ValueError:
                    print(f"Invalid update format: {update}. Use column=value")
            
            conditions = {}
            if args.where:
                for condition in args.where:
                    try:
                        column, value = condition.split("=", 1)
                        conditions[column.strip()] = value.strip()
                    except ValueError:
                        print(f"Invalid condition format: {condition}. Use column=value")
            
            db_ops.update_rows(args.table, updates, conditions)
        
        elif args.command == "list-tables":
            db_ops.list_tables()
        
        elif args.command == "list-columns":
            db_ops.list_columns(args.table)
        
        elif args.command == "count":
            conditions = {}
            if args.where:
                for condition in args.where:
                    try:
                        column, value = condition.split("=", 1)
                        conditions[column.strip()] = value.strip()
                    except ValueError:
                        print(f"Invalid condition format: {condition}. Use column=value")
            
            db_ops.count_rows(args.table, conditions)
        
        else:
            parser.print_help()
    
    finally:
        db_ops.close()

if __name__ == "__main__":
    main() 
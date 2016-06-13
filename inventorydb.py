#!/usr/bin/env python3

import logging
import os.path
import sqlite3
import sys
# import from modules created for this exercise
from constants import *

logger = logging.getLogger(__name__)
database = 'inventory.db'
    
def create_db(forcenew=False):
    """Create inventory.db with 2 tables and initialize with defaults.
    
    This should be an atomic transaction, either all tables are created successfully and
    populated with data or the transaction must be rolled-back.
    Use 'executescript' function which is more efficient, also does not need cursor.
    
    """
    if os.path.exists(database):
        if forcenew:
            os.remove(os.path.abspath(database))
        else:
            logging.warning('Database inventory.db exists, remove it, or use arg, forcenew, set to True.')
            return
        
    conn = sqlite3.connect(database)       
    try:
        # Create table using executescript statement, similar to Relational DBMS statements.
        # The script must not have Python comments inside the script.
        # Create 2 tables, one for inventory and one for orders for the product lines.
        # For this exercise, will not store valid orders in DB, but in production, it is necessary.
        with conn:
             conn.executescript("""
                  create table inventory(
                         product,
                         quantity
                  );
                  
                  insert into inventory values(
                         'A', 150
                  );
                  
                  insert into inventory values(
                         'B', 150
                  );
                  
                  insert into inventory values(
                         'C', 100
                  );
                  
                  insert into inventory values(
                         'D', 100
                  );
                  
                  insert into inventory values(
                         'E', 200
                  );
                  
                  create table orders(
                         header,
                         proda,
                         prodb,
                         prodc,
                         prodd,
                         prode
                  );
                  
                  insert into orders(
                         header,
                         proda,
                         prodb,
                         prodc,
                         prodd,
                         prode)
                         values (0, 0, 0, 0, 0, 0
                  );
             """)
    except sqlite3.OperationalError as oe:
        logging.exception('Exception when creating and populating table: %s' %(oe.args[0]))
        conn.rollback()
    except Exception as exc:
        logging.exception('Exception when creating and populating table: %s' %(exc.args[0]))
        conn.rollback()
    finally: 
        #conn.commit()   #not needed wihen using 'with con'
        conn.close()
  
    
def fetch_product_inventory(prod_name):
    """Fetch inventory data for the given product from products tables.
    
    Use Sqlite3 row_factory and retrieve only needed row.
    
    @param: The product name for which quantity in stock is needed.
    @return row: The row of inventory data for one product.
    @rtype tuple: The row with data.
    
    """  
    try:
        conn = sqlite3.connect('inventory.db')
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute('SELECT * FROM inventory where product=?', (prod_name,))
        row = cur.fetchone()
    except Exception as exc:
        logging.exception("Exception in fetch_product_inventory(): %s"  %(exc.args[0]))
    else:
        return row
    finally:
        conn.close()
        
        
def update_inventory(prod_name, new_quantity):
    """Update inventory, quantity in stock for the given product in products tables.
    
    Use Sqlite3 row_factory and retrieve only needed row.
    
    @param prod_name: The product name for which quantity is to be updated.
    @param new_quantity: The quantity to be reflected in the table row for the product.
    @return True: Return C{True} when inventory data is successfully updated.
            False: Return C{False} when inventory data is NOT successfully updated.     
    @rtype boolean: 
    
    """
    result = False
    try:
        if not isinstance(new_quantity, int):
            raise ValueError("Quantity is not integer.")
        conn = sqlite3.connect('inventory.db')
        cur = conn.cursor()
        cur.execute('UPDATE inventory set quantity = ? where product=?', (new_quantity, prod_name))
        conn.commit()
    except Exception as exc:
        if conn:
            conn.rollback()
        logging.exception("Exception in update_inventory(): %s"  %(exc.args[0]))
    else:
        result = True
    finally:       
        conn.close()
    
    return result


def fetch_full_inventory():
    """Fetch full inventory for all products to see is sum is 0.
    
    @return quantity_list: List of quantity for all 5 products.
    @rtype List
    
    """
    quantity_list = []
    try:
        conn = sqlite3.connect('inventory.db')       
        cur = conn.cursor()
        for row in cur.execute('SELECT quantity FROM inventory ORDER BY product'):
            quantity_list.append(row)
    except Exception as exc:
        logging.exception("Exception in fetch_full_inventory(): %s" %(exc.args[0]))
    else:
        return quantity_list
    finally:
        conn.close()
        
        
def fetch_all_orders():
    """Fetch all orders data from the orders table.
    
    @return orderList: List of orders for all 5 products.
    @rtype List
    """
    orderList = []
    try:
        conn = sqlite3.connect('inventory.db')       
        cur = conn.cursor()
        for row in cur.execute('SELECT * FROM orders ORDER BY header'):
            orderList.append(row)
    except Exception as exc:
        logging.exception("Exception in fetch_all_rders(): %s" %(exc.args[0]))
    else:
        return orderList
    finally:
        conn.close()
    
    
# main. This module will be imported, include function calls for unit testing.
if __name__ == '__main__':
    # if db does not exist, will not recreate it
    create_db()
     # if db exists, recreate it, useful when db schema changes.
    create_db(True)
    fetch_full_inventory()
    fetch_product_inventory('A')
    fetch_all_orders()
    update_inventory('B', 5)
    # Ensure update is successful.
    fetch_product_inventory('B')
    # update to original value
    update_inventory('B', 3)
    fetch_product_inventory('B')
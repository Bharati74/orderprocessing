"""
 orderprocessing.py  - Main Python source file for the app.
 
 App to process orders and allocate products if instock, otherwise backorder items
 not fully fulfilled. As a data source, orders are randomly generated as required.
 For testing/comparison of results, the given sample orders in the exercise are also processed;
 need to use the 'test' argument for this usecase.
 
 The modules use Multiprocessing: Manager, Process, Pool, Queue, Lock, current_process
 
 Inventory data is maintained in the Sqlite3 DB: inventory.db

    usage:
       1. python3.5 orderprocessing.py
          a. To randomly generate orders.
          b. Use database with initial defaults of large quantities (>100) as requested.
       2. python3.5 orderprocessing.py test
          a. To use sample orders given in the exercise.
          b. Upate database with smaller quantities as requested in the exercise.
          c. This will help compare the results by this app and in the exercise (proofpoint).
          
 Author: Bharati Desai
 Date:   June 9, 2016
 
"""
import logging
import multiprocessing as mp
import os
import sys

from multiprocessing import current_process, Lock, Manager, Pool, Process, Queue
from time import time

# modules developed for this app
from constants import *
from inventorydb import create_db, fetch_product_inventory, update_inventory, fetch_full_inventory
from ordersource import gen_order, validate_order

logging.basicConfig(filename='orders.log', level=logging.DEBUG,
                    format='%(asctime)s : %(name)s : %(levelname)s : %(message)s', datefmt='%Y/%m/%d %I:%M:%S %p')
logging.getLogger('orderprocessing').setLevel(logging.CRITICAL)
#logger = logging.getLogger(__name__)
logger = logging.getLogger('orderproc')

# private function for testing, must be called after initial DB is created.
def __test_sample(order_queue):
    """Test order processing using given sample DB data and orders.
    
    The inventory DB must be created prior to calling this function.
    This function updates inventory data and creates sample orders
    and puts them in the queue of orders. Processing will be continued
    by the same worker processes/functions.
    
    @param order_queue: The queue to add orders for processing, in MP Manager's control.
    
    """
    # update inventory to reflect test sample in the exercise
    update_inventory('A', 2)
    update_inventory('B', 3)
    update_inventory('C', 1)
    update_inventory('D', 0)
    update_inventory('E', 0)
    
    test_orders = [
        {"Header": 1, "Lines": [{"Product": "A", "Quantity": "1"},{"Product": "C", "Quantity": "1"}]},
        {"Header": 2, "Lines": [{"Product": "E", "Quantity": "5"}]},
        {"Header": 3, "Lines": [{"Product": "D", "Quantity": "4"}]},
        {"Header": 4, "Lines": [{"Product": "A", "Quantity": "1"},{"Product": "C", "Quantity": "1"}]},
        {"Header": 5, "Lines": [{"Product": "B", "Quantity": "3"}]},
        {"Header": 6, "Lines": [{"Product": "D", "Quantity": "4"}]}
        ]
    
    for order in test_orders:
        if validate_order(order):
            logging.info("Valid order:   %s" %(order))
            order_queue.put(order)
        else:
            logging.info("Invalid order: %s" %(order))
    
    return True
    

def display_result(hdr, ordered_d, allocated_d, backorder_d):
    """Display result including header, ordered, alllocated, backordered products."""
    # Create result such as: 1: 1,0,1,0,0::1,0,1,0,0::0,0,0,0,0
    result = str(hdr) + ': '
    order_s = ''
    alloc_s = ''
    backo_s = ''
    len1 = len(PRODUCT_NAMES)
    for j in range(len1):
        order_s = order_s + str(ordered_d[PRODUCT_NAMES[j]]) + ','
        alloc_s = alloc_s + str(allocated_d[PRODUCT_NAMES[j]]) + ','
        backo_s = backo_s + str(backorder_d[PRODUCT_NAMES[j]]) + ','

    order_s = order_s.rstrip(',')
    alloc_s = alloc_s.rstrip(',')
    backo_s = backo_s.rstrip(',')

    result = result + order_s  + '::' + alloc_s + '::' + backo_s
    logging.info("Result: %s" %(result))
    print (result)
                

def process_order(order, lock, stop_flag):
    """Process validated order using inventory data in Sqlite database.
    
    1. Get all product items with respective quantities on order.
    2. Read database inventory table to get inventory data.
    3. Fullfill line items if in stock, otherwise back order item.
    
    @param order: The valdiated order from the Manger-controlled queue to process.
    @param lock: The Manager-controlled lock to use for database access, update, etc.
    @param stop_flag: The Manager-controlled flag to indicate stop processing when inventory is 0
    
    """
    #global stop_flag_global
    # init dictionaries for oredered, allocated, and back-ordered dict
    #ordered_d = {}.join(fromkeys(PRODUCT_NAMES,0))   # works in Python 2.7 not in 3.5
    ordered_d = {x:0 for x in PRODUCT_NAMES}
    allocated_d = {x:0 for x in PRODUCT_NAMES}
    backorder_d = {x:0 for x in PRODUCT_NAMES}
    lines_needed = order[LINES]
    try:
        lock.acquire()
        for line in lines_needed:
            prod = line[PRODUCT]
            num = int(line[QUANTITY])
            pidx = str(prod)
            ordered_d[pidx] = num
            # get inventory for product from DB
            row = fetch_product_inventory(prod)
            instock = row[QUANTITY]
            if instock >= num:
                # in stock, allocate and update ordered, allocated dict                
                allocated_d[pidx] = num
                # update inventory table in DB with reduced quantity
                new_quantity = instock - num
                update_inventory(prod, new_quantity)
            elif instock > 0:
                # allocate whatever available, and backorder remaining
                allocated_d[pidx] = instock
                backorder_d[pidx] = num - instock
                new_quantity = 0
                update_inventory(prod, new_quantity)               
            else:
                # back order item, update dict
                # for this exercise, not maintaining DB table for backordered table
                backorder_d[pidx] = num         
        else:
            # check full inventory in modified DB, if all products are depleted, stop
            full_inventory_tup = fetch_full_inventory()
            sum1 = 0
            for i in range(len(full_inventory_tup)):
                sum1 += full_inventory_tup[i][0]
            if sum1 == 0:
               stop_flag['stop'] = 1
               logging.info("All products inventory is 0, stopping order processing.")
            
            display_result(order[HEADER], ordered_d, allocated_d,backorder_d)
            
    except Exception as exc:
        logging.exception("Exception in process_order(): %s" %(exc.args[0]))           
    finally:
        lock.release()
    return True


def worker(order_queue, done_queue, lock, stop_flag):
    """Each spawned process handles valid order using inventory data in Sqlite database.
    
    Algorithm:
    Queues, lock, and stop_flag are shared resources controlled by Manager.
    1. Process each order off of the queue
    2. Update done_queue for orders processed
    3. When entire inventory is exhausted, stop processing, just get orders off of the queue.
    
    """
    try:
        for order in iter(order_queue.get, 'STOP'):
            if stop_flag['stop'] == 1:
                # must exhaust getting orders out of Queue, don't process
                pass
            else:
                process_order(order, lock, stop_flag)
                done_queue.put("%s completed %s." % (current_process().name, order))
    except Exception as exc:
        done_queue.put("%s failed with: %s" % (current_process().name, exc.args[0]))    
    return True

            
def main():
    """Main function to process all orders using multiprocessing module."""
 
    # For this exercise, create new db with all initial data as expected.
    create_db(True)
               
    # when arg 'test', use DB data and sample orders in the given exercise.
    test = False
    if len(sys.argv) > 1 and sys.argv[1] == 'test':        
        test = True    
    
    ts = time()
    
    with Manager() as mgr:
        # Use Manager to controll shared resources by the processes; works for mulriple servers also.
        order_queue = mgr.Queue()
        if test:
            # Update DB with smaller quantities and create sample orders given in exercise.
            __test_sample(order_queue)
        else:
            # use pool for data source for random generation of valid/invalid orders.
            pool = Pool(CPUS)
            multiple_orders = [pool.apply_async(gen_order, ()) for i in range(20)]
            pool.close()        
            
            for order in multiple_orders:
                order_toprocess =  (order.get(timeout=1))
                if validate_order(order_toprocess):
                    logging.info("Valid order:   %s" %(order_toprocess))
                    order_queue.put(order_toprocess)
                else:
                    logging.info("Invalid order: %s" %(order_toprocess))
        
        # Common code for 'production' or 'test' orders
        # when no inventory, stop processing orders.
        # Manager , server processs, 1 for all distributed servers, is preferable.
        # Preferable to use Managers's dict, list, etc than shared memory Value, Array
        stop_flag = mgr.dict()
        stop_flag['stop'] = 0
        done_queue = mgr.Queue()
        lock = mgr.Lock()   
        for w in range(CPUS):
            p = Process(target=worker, args=(order_queue, done_queue, lock, stop_flag))
            p.start()
            order_queue.put('STOP')
            p.join()
                  
            if stop_flag['stop'] == 1:
                done_queue.put('STOP')
                #order_queue.put('STOP')
        
        done_queue.put('STOP')
    
        for i in iter(done_queue.get, 'STOP'):
            logging.info('Done queue: %s' %(i))
   
    logging.info('Completed. took %s seconds', time() - ts)


if __name__ == '__main__':
    main()

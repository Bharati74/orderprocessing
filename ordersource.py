#!/usr/bin/env python3

"""
Data/order Allocator: Generate order randamly using multiprocessing Pool class.
The orders are generated in parallel by using Pool of multprocessing.
The orders are also validated in parallel by different pool objects.
This module demonstrates both multiprocessing of order generation and validation.

"""
import logging
import random
from multiprocessing import Pool
from time import time
# from module for this app
from constants import *

logging.getLogger(__name__)
hdr = 0

def gen_order():
    """Generate an order randomly, main data source, and called by process pool.
    
    Uses random module to get random data from source containing valid and
    invalid values to simulate real life examples.
    
    @return order: The order randomly created, valid or invalid.
    @rtype dictionary: The order that contains header, list of lines for products needed.
    
    """
    global hdr
    # Header/stream of data, int in sequential number
    hdr += 1
    test_prods = []
    # valid product lines
    for i in range(len(PRODUCT_NAMES)):
        test_prods.append(PRODUCT_NAMES[i])
    # invalid product lines
    test_prods.extend(['F', 'G',])
    # num of lines to include in the order, 0-5 lines, 0 line invalid, got lots of invalid orders!
    #num_lines = random.randint(0,5)
    num_lines = random.randint(1,5)

    lines = []
    #get unique product names from the choice
    prod_sample = random.sample(test_prods, num_lines)
    for i in range(num_lines):
        prod_s = prod_sample[i]
        # quantity should be an integer in the order, but example input shows it as string
        #quana = random.randint(0,9)
        quan_s = str(random.randint(0,6))
        line = {PRODUCT : prod_s, QUANTITY : quan_s}
        lines.append(line)
    order = {HEADER : hdr, LINES : lines}
    return order

def validate_order(order):
    """validate order for accuracy before processing it.
    
    Order requirements:
    
    1. Has unique identifier, Header (per stream).
    2. Product demand is between zero and five units each of A,B,C,D, and E
       except that there must be at least one unit demanded.
       Examples of valid order:
       {"Header": 1, "Lines": {"Product": "A", "Quantity": "1"},{"Product": "C", "Quantity": "4"}} 
       
       Examples of invalide order:
       {"Header": 1, "Lines": {"Product": "B", "Quantity": "0"}}    ---> Total demand is 0
       {"Header": 1, "Lines": {"Product": "D", "Quantity": "6"}}    ---> 6 is > max 5 allowed
    
    @param order: The dictionary of order with header and product lines to be ordered.
       
    """
    try:
        # check order has 'Header' and 'Lines' as keys
        if order is None or len(order) < 2:
            logging.error('Invalid order, not all keys present: %s' %(order))
            return False
        keys = list(order.keys())
        if len(keys) != 2 and HEADER not in keys and LINES not in keys:
            logging.error('Invalid order, %s' %(order))
            return False
        
        # validate Header value
        hdr = order[HEADER]
        if not isinstance(hdr, int) or hdr < 1:
            logging.error('Invalid order, Header not integer greater than 0: %s' %(order))
            return False
       
        # validate Lines, total quantity ordered must be positive, > 0   
        lines = order[LINES]
        if len(lines) < 1:
            logging.error('Invalid order, missing product and/or quantity: %s' %(lines))
            return False
        
        quantityTotal = 0
        for line in lines:
            keys = line.keys()
            if len(keys) != 2 and PRODUCT not in keys and QUANTITY not in keys:
                logging.error('Invalid order, missing product name and/or quantity keys: %s' %(line))
                return False
            quantity = int(line[QUANTITY])
            if line[PRODUCT] not in PRODUCT_NAMES or quantity < 0 or quantity > 5:
                logging.error('Invalid order, incorrect product and/or quantity value ' %(line))
                return False
            quantityTotal += quantity      
        if quantityTotal <= 0:
            logging.error('Invalid order, total quantity ordered is 0: %s' %(order))
            return False
        
        return True
    
    except Exception as exc:
        logging.exception('Exception for %s in %s' %(exc.args[0], order))
        return False
    finally:
        # nothing to clean up yet
        pass

  
def __test_validate_order():
    """Test to validate order for unit testing."""
    
    sampleOrders = [
                    {'Header': 1, "Lines": [{"Product": "A", "Quantity": "1" },{"Product": "C", "Quantity": "1"}]},
                    {'Header': 2, "Lines": [{"Product": "B", "Quantity": "0" },{"Product": "C", "Quantity": "0"}]},
                    {'Header': 3, "Lines": [{"Product": "G", "Quantity": "1" }]},
                    {'Header': 5, "Lines": [{"Product": "D", "Quantity": "6" }]},
                    {'Header': 0, "Lines": [{"Product": "E", "Quantity": "5" },{"Product": "D", "Quantity": "1"}]},
                    {'Hdr': 1, "Lines": [{"Product": "A", "Quantity": "1" },{"Product": "C", "Quantity": "1"}]},
                    {'Header': 1, "Linesss": [{"Product": "A", "Quantity": "1" }]}
                   ]
    for order in sampleOrders:
        if validate_order(order):
            print ('Valid: %s' %(order))
        else:
            print ('Invalids: %s' %(order))
            

if __name__ == '__main__':    
    logging.info('Begins - order generation.')
    tstart = time()
    # Uncomment this test method to ensure validation works as expected
    #__test_validate_order()
    try:
        # with Pool() works in Python 3.5, gives __exit__ error in Python 2.7
        with Pool(CPUS) as pool:
            # generate multiple orders, valid/invalid, asynchronously.
            multiple_orders = [pool.apply_async(gen_order, ()) for i in range(10)]
            for order in multiple_orders:
                print (order.get(timeout=1))
            pool.close()
        logging.info('Completed unit testing order generation. Took %d seconds.' %(time() - tstart))
    except Exception as exc:
        logging.exception('Exception when generating order: %s' %(exc))
 
       
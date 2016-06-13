#!/usr/bin/env python3

"""constants to be used by all importing modules."""

import multiprocessing as mp

HEADER = 'Header'
LINES = 'Lines'
PRODUCT = 'Product'
QUANTITY = 'Quantity'
PRODUCT_NAMES = ['A', 'B', 'C', 'D', 'E']
ORDER_KEYS =  ['Product', 'Lines']
CPUS = mp.cpu_count()

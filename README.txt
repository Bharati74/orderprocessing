README.txt
Date:   June 9, 2016
Author: Bharati Desai

Readme file for the application to process orders and stop when all invenotry is zero.

Notes:
1. SQLite3 database is used for persistent data, to keep/maintain inventory data.
   More tables can be created to store orders, back-orders, but opted not to for this exercise.
2. Multiprocessing module is used heavily, uses Process, Pool, Manager and Queues, Locks as shared resources.
3. Python version 3.5.1 is used.
4. Logging is used and several log files are included.
5. Random generation of orders gives a lot of invalid orders, and can be further fine-tuned to get more valid orders.

INSTRUCTIONS:

The app is designed (arguments) to run in production mode or test mode:
    1. python3.5 orderprocessing.py
          a. To randomly generate orders.
          b. Use database with initial defaults of large quantities (>100) as requested.
   2. python3.5 orderprocessing.py test
          a. To use sample orders given in the exercise.
          b. Upate database with smaller quantities as requested in the exercise.
          c. This will help compare the results by this app and in the exercise (proofpoint).

FILES:

The files for the app are uploaded in the github directory:
The folder 'shipwire' contains:
   1. orderprocessing.py  - Main file to run
   2. inventorydb.py      - Module with functions to create invneotry.db, populate with initial data.
                            fetch one or all records from a table.
                            update row with revised quanity after product allocation.
                            performs unit testing of all functions defined (python3.5 inventory.db)
                            imported by orderprocesssing.py
   3. ordersource.py      - Module with functions to randomly generate and validate orders.
                            performs unit testing of all functions defined (python3.5 outsource.db)
                            values for random generation were updated after testing, getting more invalid orders.
                            imported by orderprocesssing.py
   4. constants.py          Constants file with commonly used constants.
                            imported by all .py files
   5. inventory.db          Database created on the fly, removed/recreated if it already exists.
   6. log files             Several log files with self-explanatory suffix containing log records 
                            For example:
                            orders.log.allinvalidorders  - all randomly generated orders are invalid,
                                                           incorrect product, invalid quantity, etc.
                                                           After this, I updated some defaults for random generation.
                            orders.log.exampledata         log file with records when using the sample orders and
                                                           DB with given small quantities in the exercise example.
                            orders.log                     log file created/updated for each run
                            

KNOWN ISSUE:
1. When inventory is zero, does not ALWAYS HALT immediately as shown below in all runs, sometimes it does,
      and at times it does not.
      The shared resource, stop_flag, controlled by Manager, is used and was used as boolean and int, but
      the root cause remains to be determined.
       
The console output is copy/pasted here (orders.log.exampledata gives log records).

/Users/bharati/samples/shipwire$python3.5 orderprocessing.py test
1: 1,0,1,0,0::1,0,1,0,0::0,0,0,0,0
2: 0,0,0,0,5::0,0,0,0,0::0,0,0,0,5
3: 0,0,0,4,0::0,0,0,0,0::0,0,0,4,0
4: 1,0,1,0,0::1,0,0,0,0::0,0,1,0,0
5: 0,3,0,0,0::0,3,0,0,0::0,0,0,0,0
6: 0,0,0,4,0::0,0,0,0,0::0,0,0,4,0
/Users/bharati/samples/shipwire$python3.5 orderprocessing.py test
1: 1,0,1,0,0::1,0,1,0,0::0,0,0,0,0
2: 0,0,0,0,5::0,0,0,0,0::0,0,0,0,5
3: 0,0,0,4,0::0,0,0,0,0::0,0,0,4,0
4: 1,0,1,0,0::1,0,0,0,0::0,0,1,0,0
5: 0,3,0,0,0::0,3,0,0,0::0,0,0,0,0
/Users/bharati/samples/shipwire$
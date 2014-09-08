charitycheck
=============

a small module for verifying an organization's ability to accept charitable contributions in the U.S. via their EIN number.

visit the [github](https://github.com/nalourie/charitycheck/).


# installation

## basic installation

```
pip install charitycheck
```

simple as that, you're now good to go! But make sure to read on for (very important) notices about module useage and getting good performance.


## Disclaimer About and Maintaining Up-to-date Information

### Returned charity status may not be up-to-date

This module uses the IRS publication 78 to perform its checks against charity EIN's. Essentially, the module downloads a copy of IRS Pub 78, unzips the file, converts the data to a quickly searchable dbm file, and then provides some functions to interface with this file. That means that the module searches its local version of Publication 78, thus if you check for a new nonprofit's charity status, it might not yet be in your database. Similarly, if a nonprofit recently lost its status, your database might not yet reflect that either. 

### How to update your charity information

To fix the above problem, you should regularly update your dbm file. This can be done by running this module as a script from the commandline:

```
python /path/to/charitycheck.py
```

(in the above command, python should be whatever command your system uses to run python scripts, of course)

or importing the function `make_dbm` and running it without arguments:

```python
from charitycheck import make_dbm

make_dbm()
````

So that you don't forget to do this regularly, we recommend setting up a cron job to do this at least less than every two weeks (14 days). You must be the judge of how important it is to make the most up to date information on these nonprofit organizations available to your module.

### Auto updating and performance

Because having up-to-date information from the IRS is so important, we've added a way for python to internally track how up-to-date your copy of publication 78 is. If you're local copy is 15 or more days out of date, then the module will automatically download a new copy and recreate the database when one of the public functions in it is called with the argument `optimize=False`, which they are all set to by default; however, creating the database can take up to several minutes, so *not regularly updating your database will unpredictably and severely affect the performance of this module, on top of increasingly jeopardize the validity of its results*.

Only you can decide how often you should update your database, but for this reason we suggest at least once every 14 days.


## Note on performance:

The module uses python's anydbm module, so for performance reasons you should make sure that you have a fast implementation of the dbm format installed to which python has access. Simply try the following imports to check:

```python 
import dbm # the classic new dbm implementation
```

```python
import gdbm # gnu dbm implementation
```

```python
import dbhash # dbm implementation found on windows in python2.7
```

If any of these imports work, you're good to go. If none of them work, this module will still operate for you, but it will use the `dumbdbm` implementation, and could be much slower. Consider getting one of the above dbm implementations in python (dbhash is also deprecated and not included in python 3).




# basic useage

The following are the public functions make available by the module:


```python
make_dbm()
```

Downloads publication 78 from the IRS, unzips it, saves the txt to disk, then converts it into a dbm file for quick useage.


```python
get_nonprofit_data(
    ein, # the nonprofit organization's ein number
	optimize=False)
```

Given an EIN, retrieves the pipe delimited string data, `"name|city|state|country|deductability code"` from the local copy of publication 78 if the organization exists, otherwise it raises a key error.

If `optimize=False`, as by default, then it also checks to make sure the local copy of publication 78 is no more than 15 days out of date, calling `make_dbm()` if the data is more out of date than 15 days.


```python
verify_nonprofit(
	ein, # the nonprofit organization's ein number
	name=None, # name of the organization **as it appears in publication 78**
	city=None, # name of the city the organization is based in
	state=None, # state abbreviation for the organization
	deductability_code=None, # the deductability code of the organization
		# (see 'explanation of data and sources' in README.md)
	optimize=False)
```

takes data about the nonprofit organization as outlined in its call signature. The EIN must always be provided, all data should be given as strings. Every piece of information provided besides the EIN is optional. The function will take the provided non-None data, and check it against organizations in the database. If an organization is found matching the provided arguments, then `verify_nonprofit` returns true, else it returns false. The optimize parameter behaves the same as in `get_nonprofit_data`.


```python
get_deductability_code(
	ein, # the nonprofit organization's ein number
	name=None, # name of the organization **as it appears in publication 78**
	city=None, # name of the city the organization is based in
	state=None, # state abbreviation for the organization
	optimize=False)
```

takes data about the nonprofit organization as outlined in its call signature, the same as with `verify_nonprofit` except that it doesn't accept a deductability code argument. Checks the provided data against organizations in the database, if a match is found, it returns the deductability code, if no match is found, it returns the empty string. The optimize parameter behaves the same as the optimize parameter for `get_nonprofit_data`.

Of course, this function can also be used to replace `verify_nonprofit` in a more extensible way, by coercing the string values returned by `get_deductability_code` to booleans.


# explanation of data and sources

The data used in this module is generated from IRS publication 78, located at http://apps.irs.gov/app/eos/forwardToPub78Download.do.

The format of the file at that download site is expected to be a zipped folder, containing a text file, whose names are both data-download-pub78.zip and data-download-pub78.txt respectively, with data-download-pub78.txt being a textfile with a charity on each line, and every line having the format: 

```
EIN|name|city|state|country|deductability code
```

If any of these assumptions change, the code may need to change accordingly

From the IRS website, here is an explanation of the deductability status codes:

```
-----------------------------------------------------------------------------------------------
| Code    |    Type of organization and use of contribution.    |    Deductibility Limitation |
-----------------------------------------------------------------------------------------------
| PC      |    A public charity.	                            |    50%                      |
-----------------------------------------------------------------------------------------------
| POF	  |    A private operating foundation.	                |    50%                      |
-----------------------------------------------------------------------------------------------             
| PF	  |    A private foundation.                            |    30% (generally)          |
----------------------------------------------------------------------------------------------- 
| GROUP	  |    Generally, a central organization holding a group|                             |
|         |    exemption letter, whose subordinate units covered|                             |
|         |    by the group exemption are also eligible to      | Depends on various factors. |
|         |    receive tax-deductible contributions, even though|                             |
|         |    they are not separately listed.	                |                             |
-----------------------------------------------------------------------------------------------
| LODGE	  |    A domestic fraternal society, operating under the|                             |
|         |    lodge system, but only if the contribution is to |    30%                      |
|         |    be used exclusively for charitable purposes.	    |                             |
-----------------------------------------------------------------------------------------------
| UNKWN	  |    A charitable organization whose public charity   | Depends on various factors. |
|         |    status has not been determined.	                |                             |
-----------------------------------------------------------------------------------------------
| EO      |    An organization described in section 170(c) of   |                             |
|         |    the Internal Revenue Code other than a public    | Depends on various factors. |
|         |    charity or private foundation.                   |                             |
-----------------------------------------------------------------------------------------------
| FORGN	  |    A foreign-addressed organization. These are      |                             | 
|         |    generally organizations formed in the United     |                             | 
|         |    States that conduct activities in foreign        |                             | 
|         |    countries. Certain foreign organizations that    | Depends on various factors. |
|         |    receive charitable contributions deductible      |                             | 
|         |    pursuant to treaty are also included, as are     |                             | 
|         |    organizations created in U.S. possessions.       |                             | 
-----------------------------------------------------------------------------------------------
| SO      |    A Type I, Type II, or functionally integrated    |    50%                      |
|         |    Type III supporting organization.                |                             |
-----------------------------------------------------------------------------------------------
| SONFI	  |    A non-functionally integrated Type III           |    50%                      |
|         |    supporting organization.                         |                             |
-----------------------------------------------------------------------------------------------
| SOUNK	  |    A supporting organization, unspecified type.	    |    50%                      |
-----------------------------------------------------------------------------------------------

# contributors

So far this module has been developed only by Nicholas Lourie, but if other people are interested in helping to extend it to a larger framework for dealing with nonprofit data, pull requests are welcome!
```
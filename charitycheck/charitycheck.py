"""
charitycheck: a small module for verifying
an organization's ability to accept charitable
contributions in the U.S. via their EIN number.
"""

import anydbm as dbm
import urllib2
import io
import zipfile
import datetime
from functools import wraps
import os


# Keep these variables up-to-date

# the url of the IRS publication 78, assumed to
# be a zip folder containing a text file of
# publication 78, in the format:
#    EIN|name|city|state abbreviation|country|deductability code
IRS_NONPROFIT_DATA_URL=(
    "http://apps.irs.gov/"
    "pub/epostcard/data-download-pub78.zip")

# the name that the irs gives to the text file
# version of publication 78 contained in their
# zip file download
TXT_FILE_NAME="data-download-pub78.txt"

# variable to configure where you want publication
# 78 and its update log to be stored on disk
DATA_LOCATION=os.path.join(
    os.path.dirname(__file__), "data")

# dynamically generated path to the irs publication
# 78 file, do not edit/change this variable.
_irs_data_path = os.path.join(
    DATA_LOCATION, TXT_FILE_NAME)

# name of the file containing the dates on
# which the irs data was updated.
UPDATE_LOG_NAME = "update-log.txt"

# dynamically generate path to the update log
_update_log = os.path.join(
    DATA_LOCATION, UPDATE_LOG_NAME)

# name of the database/dbm to generate from
# publication 78
PUBLICATION78_DBM_NAME = "IRSPublication78.dbm"

# dynamically generate path to dbm file
_publication78_dbm = os.path.join(
    DATA_LOCATION, PUBLICATION78_DBM_NAME)


class IRSNonprofitDataContextManager(object):
    """a context manager for the nonprofit data
    (EINs and other identifying information)
    contained in IRS Publication 78.

    Returns publication 78 as a file-like object,
    opened for reading, downloading and unzipping
    a new copy of it every time, to catch new
    updates.
    """

    def _download_irs_nonprofit_data(self):
        """internal method downloading the irs
        publication 78 data, unzipping it, and
        writing the txt file to disk.

        To use the irs publication 78 data, you
        should use the irs_nonprofit_data context
        manager, which will automatically download
        the data if it is 15 days or more days out
        of date.
        """
        # with statements are not supported on
        # some of these filetypes, so need to
        # (messily) use try finally clauses.
        try:
            # download IRS data
            irs_url_data = urllib2.urlopen(
                IRS_NONPROFIT_DATA_URL)
            try:
                # convert IRS data to proper format
                irs_zip_data = io.BytesIO(
                    irs_url_data.read())
                try:
                    # extract zipfile from IRS data
                    z = zipfile.ZipFile(irs_zip_data)
                    z.extract(member=TXT_FILE_NAME,
                              path=DATA_LOCATION)
                finally:
                    z.close()
            finally:
                irs_zip_data.close()
        finally:
            irs_url_data.close()
    
    def __enter__(self):
        # always get fresh copy of publication 78
        # before using it. This context manager
        # should only be used by functions/methods
        # meant to run asynchronously like _make_dbm.
        self._download_irs_nonprofit_data()
        self.pub78 = open(_irs_data_path, 'r')
        return self.pub78

    def __exit__(self, exc_type, exc_value, traceback):
        self.pub78.close()


def make_dbm():
    with IRSNonprofitDataContextManager() as irs_data:
        # always create a new dbm file, rather than
        # updating an existing one.
        db = dbm.open(_publication78_dbm, 'n')
        next(irs_data)
        next(irs_data) # skip first two lines (\n chars)
        for nonprofit in irs_data:
            # map the EIN to the rest of the nonprofit
            # data, dropping pipe delimiter between the
            # EIN and the nonprofit's name, and the \n
            # character on the end of the line.
            db[nonprofit[0:9]] = nonprofit[10:-1]
        db.close()
        # log the date/time that the dbm file was updated,
        # creating the file if it doesn't exist.
        with open(_update_log, 'a') as log:
            log.write(str(datetime.datetime.today()))


def get_nonprofit_data(ein, optimize=False):
    """using an EIN, get the nonprofit's
    data from IRS publication 78.
    
    Takes optional argument optimize, if optimize is
    set to true, the function won't check whether or
    not the publication 78 information is up-to-date.
    Do this only if you have set a cron job to
    regularly update the info.

    If optimize=False (as it does by
    default), then the function will download a fresh
    copy of pub78 and preprocess it, if the information
    is out-of-date.
    """
    # avoid potentially expensive IO operation if optimization
    # is desired.
    if not optimize:
        # try to get the most recent update
        try:
            # find the last time that the dbm file was updated.
            with open(_update_log, 'r') as log:
                log.seek(-26, 2)
                date_string = log.read()
                last_updated = datetime.datetime(
                    # convert/unpack date_string into
                    # the proper format.
                    *(map(int, [date_string[0:4],
                                date_string[5:7],
                                date_string[8:10],
                                date_string[11:13],
                                date_string[14:16],
                                date_string[17:19],
                                date_string[20:]])))
            # check if the data is 15 days or more out of date,
            # since we agree to give the cron job at least 14
            # days to update it.
            if(datetime.datetime.today() - last_updated >=
               datetime.timedelta(15)):
                make_dbm()
        # if the update log has not been created, or has no
        # updates in it, we must create the log and the dbm
        # file.
        except(IOError):
            # create dbm/create log/add update to log.
            make_dbm()
    db = dbm.open(_publication78_dbm, 'r')
    output = db[ein]
    db.close()
    return output


def verify_nonprofit(
    ein, name=None, city=None, state=None, country=None,
    deductability_code=None, optimize=False):
    """take various information about an organization
    as described in the function's parameters, and
    verify that such an organization is indeed
    registered as a nonprofit with the irs with that
    information, returning a boolean True or False

    Takes optional argument optimize, if optimize is
    set to true, the function won't check whether or
    not the publication 78 information is up-to-date.
    Do this only if you have set a cron job to
    regularly update the info.

    If optimize=False (as it does by
    default), then the function will download a fresh
    copy of pub78 and preprocess it, if the information
    is out-of-date.)
    """
    try:
        # create a list of the nonprofit's info
        nonprofit_data = get_nonprofit_data(
            ein, optimize).split('|')
        boolean = True
        for i, info in enumerate((name, city, state, country,
                     deductability_code)):
            if info != None:
                boolean = boolean and info == nonprofit_data[i]
        return boolean
    except(KeyError):
        # if the ein is not in the database...
        return False


def get_deductability_code(
    ein, name=None, city=None, state=None,
    country=None, optimize=False):
    """take various information about an organization as
    described by the function's paramters, and return the
    deductability code of that nonprofit, or the empty
    string if that nonprofit is not registered with the
    IRS.

    Takes optional argument optimize, if optimize is
    set to true, the function won't check whether or
    not the publication 78 information is up-to-date.
    Do this only if you have set a cron job to
    regularly update the info.

    If optimize=False (as it does by
    default), then the function will download a fresh
    copy of pub78 and preprocess it, if the information
    is out-of-date.)
    """
    try:
        # create a list of nonprofit's info
        nonprofit_data = get_nonprofit_data(
            ein, optimize).split('|')
        is_registered_nonprofit = True
        for i, info in enumerate((name, city, state, country)):
            if info != None:
                is_registered_nonprofit = (
                    is_registered_nonprofit and info == nonprofit_data[i])
        if is_registered_nonprofit:
            return nonprofit_data[-1]
        else:
            return ''
    except(KeyError):
        return ''
                
    
# run the module as a script to make the database:
if __name__ == '__main__':
    print 'creating IRS Publication 78 dbm'
    make_dbm()
    print 'IRS Publication 78 dbm created'
    
#
## unused, but potentially useful code:
#

# created a decorator to check if the irs
# data is up-to-date, but don't use it since
# the code is never duplicated (although it was
# in a previous implementation) and for
# performance reasons.
def check_pub78_data_up_to_date(func):
    """decorator to implement the pattern of
    verifying that the local copy of publication
    78 is up-to-date before running a function.
    """
    @wraps(func) # update the 'inner' function's metadata
    def inner(optimize=False, *args, **kwargs):
        # save potentially expensive IO operation if optimization
        # is desired.
        if not optimize:
            # try to get the most recent update
            try:
                # find the last time that the dbm file was updated.
                with open(_update_log, 'r') as log:
                    log.seek(-26, 2)
                    last_updated = log.read(str(datetime.datetime.today()))
                # check if the data is 15 days or more out of date,
                # since we agree to give the cron job at least 14
                # days to update it.
                if(datetime.datetime.today() - last_updated >=
                   datetime.timedelta(15)):
                    make_dbm()
            # if the update log has not been created, or has no
            # updates in it, we must create the log and the dbm
            # file.
            except(IOError):
                make_dbm()
        func(*args, **kwargs)
    return inner

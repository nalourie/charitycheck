import unittest
import charitycheck
import re
import datetime
import anydbm as dbm

class TestIRSNonprofitDataContextManager(unittest.TestCase):

    # we break test the principle of keeping tests
    # independent below, sometimes with good reason,
    # sometimes for convenience because this is a small
    # module. These tests should not be run while the module
    # is in use.
    def test__download_irs_nonprofit_data(self):
        # get fresh copy of irs and check for exceptions
        # in writing permissions, internet connections,
        # etc...
        charitycheck.IRSNonprofitDataContextManager(
            )._download_irs_nonprofit_data()
        # signal that the test passed
        self.assertTrue(True)

    def test_context_manager_updates_data(self):
        """check that opening the context manager
        updates the local irs pub78 data.
        """
        with open(charitycheck._irs_data_path, 'a+') as irs_data:
            irs_data.write("TESTSTRING_FOR_CHARITYCHECK")
            found_test_phrase = False
            irs_data.seek(-27, 2)
            for line in irs_data:
                if "TESTSTRING_FOR_CHARITYCHECK" in line:
                    found_test_phrase = True
            self.assertTrue(found_test_phrase)
            with charitycheck.IRSNonprofitDataContextManager() as new_irs_data:
                # see if we've overwritten the old file
                found_test_phrase = False
                for line in new_irs_data:
                    if "TESTSTRING_FOR_CHARITYCHECK" in line:
                        found_test_phrase = True
                # assert that the test phrase has been overwritten
                self.assertFalse(found_test_phrase)

    def test_file_format(self):
        """check that the file downloaded from the IRS
        is in the format we expect.
        """
        with charitycheck.IRSNonprofitDataContextManager() as irs_data:
            in_expected_format = True
            # check first two lines are \n characters
            in_expected_format = (in_expected_format and
                                  irs_data.readline() == '\n')
            in_expected_format = (in_expected_format and
                                  irs_data.readline() == '\n')
            for i, line in enumerate(irs_data):
                m = re.match(
                    r'^(?:\d{9}\|.+\|.+(?:\|[A-Z]{2})?\|.+\|(?:[A-Z],?)+''\n|\n)$',
                    line)
                in_expected_format = in_expected_format and bool(m)
            self.assertTrue(in_expected_format)


class TestMakeDBM(unittest.TestCase):

    def test_make_dbm(self):
        charitycheck.make_dbm() # catch any possible errors/exceptions
        self.assertTrue(True)

    def test_log_updates(self):
        # get last updated time
        with open(charitycheck._update_log, 'r') as log:
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
        # run make dbm
        charitycheck.make_dbm()
        # get new updated time
        with open(charitycheck._update_log, 'r') as log:
            log.seek(-26, 2)
            date_string = log.read()
            new_last_updated = datetime.datetime(
                # convert/unpack date_string into
                # the proper format.
                *(map(int, [date_string[0:4],
                            date_string[5:7],
                            date_string[8:10],
                            date_string[11:13],
                            date_string[14:16],
                            date_string[17:19],
                            date_string[20:]])))
        self.assertNotEqual(last_updated, new_last_updated)
        
    def test_dbm_has_all_charities(self):
        with open(charitycheck._irs_data_path) as irs_data:
            nonprofits_present = True
            db = dbm.open(charitycheck._publication78_dbm, 'r')
            for nonprofit in irs_data:
                nonprofits_present = (
                    nonprofits_present and
                    db[nonprofit[0:9]] == nonprofit[10:-1])
            db.close()
            self.assertTrue(nonprofits_present)


class TestGetNonprofitData(unittest.TestCase):

    def test_nonprofits_info_is_found(self):
        self.assertEqual(
            # assume the red cross will be around awhile...
            charitycheck.get_nonprofit_data('530196605'),
            'American National Red Cross|Charlotte|NC|United States|PC')


class TestVerifyNonprofit(unittest.TestCase):

    def test_verify_nonprofit_all_arguments_when_true(self):
        self.assertTrue(charitycheck.verify_nonprofit(
            ein='530196605', name='American National Red Cross',
            city='Charlotte', state='NC', country='United States',
            deductability_code='PC'))

    def test_verify_nonprofit_some_arguments_when_true_1(self):
        self.assertTrue(charitycheck.verify_nonprofit(
            ein='530196605', name='American National Red Cross',
            city='Charlotte', state='NC', country='United States',
            deductability_code=None))

    def test_verify_nonprofit_some_arguments_when_true_2(self):
        self.assertTrue(charitycheck.verify_nonprofit(
            ein='530196605', name='American National Red Cross',
            city='Charlotte', state='NC', country=None,
            deductability_code=None))

    def test_verify_nonprofit_some_arguments_when_true_3(self):
        self.assertTrue(charitycheck.verify_nonprofit(
            ein='530196605', name='American National Red Cross',
            city='Charlotte'))

    def test_verify_nonprofit_some_arguments_when_true_4(self):
        self.assertTrue(charitycheck.verify_nonprofit(
            ein='530196605', name='American National Red Cross'))

    def test_verify_nonprofit_some_arguments_when_true_5(self):
        self.assertTrue(charitycheck.verify_nonprofit(
            ein='530196605', state='NC', country='United States',
            deductability_code='PC'))

    def test_verify_nonprofit_some_arguments_when_true_6(self):
        self.assertTrue(charitycheck.verify_nonprofit(
            ein='530196605', name=None,
            city='Charlotte', state='NC', country='United States',
            deductability_code='PC'))

    def test_verify_nonprofit_some_arguments_when_true_7(self):
        self.assertTrue(charitycheck.verify_nonprofit(
            ein='530196605', name='American National Red Cross',
            city=None, state=None, country='United States',
            deductability_code=None))

    def test_verify_nonprofit_just_ein_when_true(self):
        self.assertTrue(charitycheck.verify_nonprofit(
            ein='530196605'))

    def test_verify_nonprofit_some_arguments_when_false(self):
        self.assertFalse(charitycheck.verify_nonprofit(
            ein='530196605', name='American National Red Cross',
            city='Boston')) # city is a false argument

    def test_verify_nonprofit_bad_ein(self):
        self.assertFalse(charitycheck.verify_nonprofit(ein='4'))


class TestGetDeductabilityCode(unittest.TestCase):

    def test_get_deductability_code_all_arguments_true(self):
        self.assertEqual(
            charitycheck.get_deductability_code(
                ein='530196605', name='American National Red Cross',
                city='Charlotte', state='NC', country='United States'),
            'PC')

    def test_get_deductability_code_some_arguments_when_true_1(self):
        self.assertEqual(
            charitycheck.get_deductability_code(
                ein='530196605', name='American National Red Cross',
                city=None, state='NC', country='United States'),
            'PC')

    def test_get_deductability_code_some_arguments_when_true_2(self):
        self.assertEqual(
            charitycheck.get_deductability_code(
                ein='530196605', name='American National Red Cross',
                city='Charlotte', state='NC', country=None),
            'PC')

    def test_get_deductability_code_some_arguments_when_true_3(self):
        self.assertEqual(
            charitycheck.get_deductability_code(
                ein='530196605', name='American National Red Cross',
                city='Charlotte'),
            'PC')

    def test_get_deductability_code_some_arguments_when_true_4(self):
        self.assertEqual(
            charitycheck.get_deductability_code(
                ein='530196605', name='American National Red Cross'),
            'PC')

    def test_get_deductability_code_some_arguments_when_true_5(self):
        self.assertEqual(
            charitycheck.get_deductability_code(
                ein='530196605', state='NC', country='United States'),
            'PC')

    def test_get_deductability_code_some_arguments_when_true_6(self):
        self.assertEqual(
            charitycheck.get_deductability_code(
                ein='530196605', name=None,
                city='Charlotte', state='NC', country='United States'),
            'PC')

    def test_get_deductability_code_some_arguments_when_true_7(self):
        self.assertEqual(
            charitycheck.get_deductability_code(
                ein='530196605', name='American National Red Cross',
                city=None, state=None, country='United States'),
            'PC')

    def test_get_deductability_code_just_ein_when_true(self):
        self.assertEqual(
            charitycheck.get_deductability_code(
                ein='530196605'),
            'PC')

    def test_get_deductability_code_some_arguments_when_false(self):
        self.assertEqual(
            charitycheck.get_deductability_code(
                ein='530196605', name='American National Red Cross',
                city='Boston'), # city is a false argument
            '') 

    def test_get_deductability_code_bad_ein(self):
        self.assertEqual(
            charitycheck.get_deductability_code(
                ein='6'),
            '')

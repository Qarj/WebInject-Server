# Create your tests here.

from django.test import TestCase
from django.urls import reverse
from django.utils.http import urlencode

import re

#
# Test Helpers
#

# https://stackoverflow.com/questions/4995279/including-a-querystring-in-a-django-core-urlresolvers-reverse-call
def my_reverse(viewname, kwargs=None, query_kwargs=None):
    """
    Custom reverse to add a query string after the url
    Example usage:
    url = my_reverse('my_test_url', kwargs={'pk': object.id}, query_kwargs={'next': reverse('home')})
    """
    url = reverse(viewname, kwargs=kwargs)

    if query_kwargs:
        return u'%s?%s' % (url, urlencode(query_kwargs))

    return url

class ServerIndexViewTests(TestCase):
    def test_index(self):
        """
        Server index page exists
        """
        response = self.client.get(reverse('server:index'))
        self.assertEqual(response.status_code, 200)

class RunWebInjectFrameWorkTests(TestCase):
    
    #
    # test helpers
    #

    def runit(self, path, debug=False):
        url = my_reverse('server:run', query_kwargs={'path': path})
        return self._get_url(url, debug)

    def _get_url(self, url, debug=False):
        response = self.client.get(url)
        if (debug):
            print('\nDebug URL:', url)
            print(response.content.decode('utf-8'), '\n')
        return response

    def number_of_instances(self, response, target):
        return response.content.decode('utf-8').count(target)

    def _assertRegex(self, response, regex):
        self.assertRegex(response.content.decode('utf-8'), regex)

    def _assertNotRegex(self, response, regex):
        self.assertNotRegex(response.content.decode('utf-8'), regex)

    #
    # Run WebInject Framework Tests
    #

    def test_run_simple_test_in_webinject_examples(self):
        response = self.runit('examples/test.xml', True)
        self.assertContains(response, 'Test that WebInject can run a very basic test')
        self.assertContains(response, '<pre><code>')
        self.assertContains(response, '</code></pre>')
        self.assertContains(response, 'Result at: http')
        self._assertRegex(response, r'\sFailed Positive Verification') # i.e. no ANSI code like 1;33m
        self.assertContains(response, 'style.css')

# \Apache24\bin\httpd -k restart

# Post POC Hardening Tests
#   - Add a favicon
#   - Prepend a WEBINJECT TEST PASSED or WEBINJECT TEST FAILED message (in correct colours)
#   - Prepend a WEBINJECT ERROR message, return 500 (in red)
#   - Add appropriate wif.pl switches
#   - Multi proto should be in a different batch
#   - Can supply custom batch name
#   - Can supply custom target
#   - Search for wif.pl in known installation locations
#   - Index page gives examples of how to run tests
#   - Result location parsed out and made clickable, prepended
#   - Time that it takes to run slow displayed on index


# MVP Tests
#   - POST URL server/submit with POSTBODY of webinject test cases.
#   - form for posting a test


## https://cgoldberg.github.io/python-unittest-tutorial/

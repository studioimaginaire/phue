# Published under the MIT license - See LICENSE file for more detail
#
# This is a basic test file which just tests that things import, which
# means that this is even vaguely python code.

import fixtures
import mock
import os
import testtools

import phue


class TestRequest(testtools.TestCase):

    def setUp(self):
        super(TestRequest, self).setUp()
        self.home = fixtures.TempHomeDir()
        self.useFixture(self.home)

    def test_register(self):
        """test that registration happens automatically during setup."""
        confname = os.path.join(self.home.path, '.python_hue')
        with mock.patch("phue.Bridge.request") as req:
            req.return_value = [{'success': {'username': 'fooo'}}]
            bridge = phue.Bridge(ip="10.0.0.0")
            self.assertEqual(bridge.config_file_path, confname)

        # check contents of file
        with open(confname) as f:
            contents = f.read()
            self.assertEqual(contents, '{"10.0.0.0": {"username": "fooo"}}')

        # make sure we can open under a different file
        bridge2 = phue.Bridge(ip="10.0.0.0")
        self.assertEqual(bridge2.username, "fooo")

        # and that we can even open without an ip address
        bridge3 = phue.Bridge()
        self.assertEqual(bridge3.username, "fooo")
        self.assertEqual(bridge3.ip, "10.0.0.0")

    def test_register_fail(self):
        """Test that registration fails in the expected way for timeout"""
        with mock.patch("phue.Bridge.request") as req:
            req.return_value = [{'error': {'type': 101}}]
            self.assertRaises(phue.PhueRegistrationException,
                              phue.Bridge, ip="10.0.0.0")

    def test_register_unknown_user(self):
        """Test that registration for unknown user works."""
        with mock.patch("phue.Bridge.request") as req:
            req.return_value = [{'error': {'type': 7}}]
            self.assertRaises(phue.PhueException,
                              phue.Bridge, ip="10.0.0.0")

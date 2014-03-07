# Copyright 2014 Google Inc. All rights reserved.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import unicode_literals

import caniusepython3.__main__ as ciu_main

import io
import logging
import tempfile
import unittest
try:
    from unittest import mock
except ImportError:
    import mock


EXAMPLE_REQUIREMENTS = """
# From
#  http://www.pip-installer.org/en/latest/reference/pip_install.html#requirement-specifiers
# but without the quotes for shell protection.
FooProject >= 1.2
Fizzy [foo, bar]
PickyThing<1.6,>1.9,!=1.9.6,<2.0a0,==2.4c1
Hello
-e git+https://github.com/brettcannon/caniusepython3#egg=caniusepython3
file:../caniusepython3#egg=caniusepython3
# Docs say to specify an #egg argument, but apparently it's optional.
file:../../lib/project
"""

EXAMPLE_METADATA = """Metadata-Version: 1.2
Name: CLVault
Version: 0.5
Summary: Command-Line utility to store and retrieve passwords
Home-page: http://bitbucket.org/tarek/clvault
Author: Tarek Ziade
Author-email: tarek@ziade.org
License: PSF
Keywords: keyring,password,crypt
Requires-Dist: foo; sys.platform == 'okook'
Requires-Dist: bar
Platform: UNKNOWN
"""

class CLITests(unittest.TestCase):

    expected_requirements = frozenset(['FooProject', 'Fizzy', 'PickyThing',
                                       'Hello'])
    expected_metadata = frozenset(['foo', 'bar'])

    def setUp(self):
        log = logging.getLogger('ciu')
        self._prev_log_level = log.getEffectiveLevel()
        logging.getLogger('ciu').setLevel(1000)

    def tearDown(self):
        logging.getLogger('ciu').setLevel(self._prev_log_level)

    def test_requirements(self):
        with tempfile.NamedTemporaryFile('w') as file:
            file.write(EXAMPLE_REQUIREMENTS)
            file.flush()
            got = ciu_main.projects_from_requirements([file.name])
        self.assertEqual(set(got), self.expected_requirements)

    def test_multiple_requirements_files(self):
        with tempfile.NamedTemporaryFile('w') as f1:
            with tempfile.NamedTemporaryFile('w') as f2:
                f1.write(EXAMPLE_REQUIREMENTS)
                f2.write('foobar\n')
                f2.flush()
                got = ciu_main.projects_from_requirements([f1.name, f2.name])
        expected_requirements = frozenset(
            list(self.expected_requirements) + ['foobar']
        )
        self.assertEqual(set(got), expected_requirements)

    def test_metadata(self):
        got = ciu_main.projects_from_metadata(EXAMPLE_METADATA)
        self.assertEqual(set(got), self.expected_metadata)

    def test_cli_for_requirements(self):
        with tempfile.NamedTemporaryFile('w') as file:
            file.write(EXAMPLE_REQUIREMENTS)
            file.flush()
            args = ['--requirements', file.name]
            got = ciu_main.projects_from_cli(args)
        self.assertEqual(set(got), self.expected_requirements)

    def test_cli_for_metadata(self):
        with tempfile.NamedTemporaryFile('w') as file:
            file.write(EXAMPLE_METADATA)
            file.flush()
            args = ['--metadata', file.name]
            got = ciu_main.projects_from_cli(args)
        self.assertEqual(set(got), self.expected_metadata)

    def test_cli_for_projects(self):
        args = ['--projects', 'foo,bar']
        got = ciu_main.projects_from_cli(args)
        self.assertEqual(set(got), frozenset(['foo', 'bar']))

    def test_message_plural(self):
        blockers = [['A'], ['B']]
        messages = ciu_main.message(blockers)
        self.assertEqual(2, len(messages))
        want = 'You need 2 projects to transition to Python 3.'
        self.assertEqual(messages[0], want)
        want = ('Of those 2 projects, 2 have no direct dependencies blocking '
                'their transition:')
        self.assertEqual(messages[1], want)

    def test_message_plural(self):
        blockers = [['A']]
        messages = ciu_main.message(blockers)
        self.assertEqual(2, len(messages))
        want = 'You need 1 project to transition to Python 3.'
        self.assertEqual(messages[0], want)
        want = ('Of that 1 project, 1 has no direct dependencies blocking '
                'its transition:')
        self.assertEqual(messages[1], want)

    def test_message_no_blockers(self):
        messages = ciu_main.message([])
        self.assertEqual(
            ['You have 0 projects blocking you from using Python 3!'],
            messages)

    def test_pprint_blockers(self):
        simple = [['A']]
        fancy = [['A', 'B']]
        nutty = [['A', 'B', 'C']]
        repeated = [['A', 'C'], ['B']]  # Also tests sorting.
        got = ciu_main.pprint_blockers(simple)
        self.assertEqual(list(got), ['A'])
        got = ciu_main.pprint_blockers(fancy)
        self.assertEqual(list(got), ['A (which is blocking B)'])
        got = ciu_main.pprint_blockers(nutty)
        self.assertEqual(list(got),
                         ['A (which is blocking B, which is blocking C)'])
        got = ciu_main.pprint_blockers(repeated)
        self.assertEqual(list(got), ['B', 'A (which is blocking C)'])

    @mock.patch('argparse.ArgumentParser.error')
    def test_projects_must_be_specified(self, parser_error):
        ciu_main.projects_from_cli([])
        self.assertEqual(
            mock.call("Missing 'requirements', 'metadata', or 'projects'"),
            parser_error.call_args)


#@unittest.skip('faster testing')
class NetworkTests(unittest.TestCase):

    @mock.patch('sys.stdout', io.StringIO())
    def test_e2e(self):
        # Make sure at least one project that will never be in Python 3 is
        # included.
        args = '--projects', 'numpy,scipy,matplotlib,ipython,paste'
        ciu_main.main(args)


if __name__ == '__main__':
    unittest.main()

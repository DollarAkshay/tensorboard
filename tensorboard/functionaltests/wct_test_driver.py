# Copyright 2018 The TensorFlow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""WebDriver for running TypeScript and Polymer unit tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import re
import subprocess
import unittest
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support import wait
from testing.web import webtest


# As emitted in the "Listening on:" line of the WebfilesServer output.
# We extract only the port because the hostname can reroute through corp
# DNS and force auth, which fails in tests.
_URL_RE = re.compile(r'http://[^:]*:([0-9]+)/')


def create_test_class(binary_path, web_path):
  """Create a unittest.TestCase class to run WebComponentTester tests.

  Arguments:
    binary_path: relative path to a `tf_web_library` target containing
        the tests; e.g.: "tensorboard/components/vz_foo/test/test"
    web_path: absolute web path to the tests page in the above web
        library; e.g.: "/vz-foo/test/tests.html"

  Result:
    A new subclass of `unittest.TestCase`. Bind this to a variable in
    the test file's main module.
  """

  class WebComponentTesterTest(unittest.TestCase):
    """Tests that the basic chrome is displayed when there is no data."""

    def setUp(cls):
      src_dir = os.environ["TEST_SRCDIR"]
      binary = os.path.join(
          src_dir,
          "org_tensorflow_tensorboard/" + binary_path)
      cls.process = subprocess.Popen(
          [binary], stdin=None, stdout=None, stderr=subprocess.PIPE)
      while True:
        line = cls.process.stderr.readline()
        match = _URL_RE.search(line)
        if match:
          cls.port = match.group(1)
          break

    def tearDown(cls):
      cls.process.kill()
      cls.process.wait()

    def test(self):
      driver = webtest.new_webdriver_session()
      url = "http://localhost:%s%s" % (self.port, web_path)
      driver.get(url)
      wait.WebDriverWait(driver, 10).until(
          expected_conditions.title_contains("test"))
      title = driver.title
      if "failing test" in title or "passing test" not in title:
        self.fail(title)

  return WebComponentTesterTest

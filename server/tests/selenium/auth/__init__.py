# This file is part of sner4 project governed by MIT license, see the LICENSE.txt file.
"""
auth.views selenium tests shared functions
"""


class js_variable_ready():  # pylint: disable=invalid-name,too-few-public-methods
    """custom expected_condition, wait for variable/object"""

    def __init__(self, variable):
        self.variable = variable

    def __call__(self, driver):
        return driver.execute_script(f'return({self.variable} !== undefined);')

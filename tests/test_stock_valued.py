# This file is part of the stock_valued module for Tryton.
# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
import unittest
import trytond.tests.test_tryton
from trytond.tests.test_tryton import ModuleTestCase


class StockValuedTestCase(ModuleTestCase):
    'Test Stock Valued module'
    module = 'stock_valued'


def suite():
    suite = trytond.tests.test_tryton.suite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
        StockValuedTestCase))
    return suite
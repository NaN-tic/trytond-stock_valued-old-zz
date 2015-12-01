#!/usr/bin/env python
# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
import unittest
import trytond.tests.test_tryton
from trytond.tests.test_tryton import test_depends, test_view


class StockValuedTestCase(unittest.TestCase):
    'Test Stock Valued module'

    def setUp(self):
        trytond.tests.test_tryton.install_module('stock_valued')

    def test0005view(self):
        'Test view'
        test_view('stock_valued')

    def test0006depends(self):
        'Test depends'
        test_depends()


def suite():
    suite = trytond.tests.test_tryton.suite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
        StockValuedTestCase))
    return suite
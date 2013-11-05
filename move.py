#This file is part stock_valued module for Tryton.
#The COPYRIGHT file at the top level of this repository contains
#the full copyright notices and license terms.
from trytond.model import fields
from trytond.pyson import Not, Equal, Eval, Bool
from trytond.pool import Pool, PoolMeta
from decimal import Decimal

__all__ = ['Move']
__metaclass__ = PoolMeta

_ZERO = Decimal('0.0')


class Move:
    "Stock Move"
    __name__ = 'stock.move'

    amount = fields.Function(fields.Numeric('Amount',
            digits=(16, 4),
            states={
                'invisible': Not(Bool(Eval('state') == 'done')),
                }), 'get_amount')

    def get_amount(self, name):
        Currency = Pool().get('currency.currency')
        res = _ZERO
        if self.quantity:
            res = Currency.round(
                    self.company.currency,
                    Decimal(str(self.quantity)) * self.unit_price)
        return res

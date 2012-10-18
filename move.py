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
                'invisible': Not(Bool(Eval('unit_price_required'))),
                'required': Bool(Eval('unit_price_required')),
                'readonly': Not(Equal(Eval('state'), 'draft')),
                }, on_change_with=['quantity', 'unit_price'],
            ),'get_amount')

    def on_change_with_amount(self, name=None):
        Currency = Pool().get('currency.currency')
        if self.quantity and self.unit_price:
            currency = (vals.get('_parent_invoice.currency')
                or self.currency)
            if isinstance(currency, (int, long)) and currency:
                currency = Currency.browse(currency)
            amount = Decimal(str(self.quantity or '0.0')) * \
                    (self.unit_price or Decimal('0.0'))
            if currency:
                return Currency.round(currency, amount)
            return amount
        return Decimal('0.0')

    def get_amount(self, name):
        Currency = Pool().get('currency.currency')
        res = _ZERO
        if self.quantity:
            res = Currency.round(
                    self.company.currency,
                    Decimal(str(self.quantity)) * self.unit_price)
        return res

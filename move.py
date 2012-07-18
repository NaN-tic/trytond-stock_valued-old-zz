#This file is part stock_valued module for Tryton.
#The COPYRIGHT file at the top level of this repository contains 
#the full copyright notices and license terms.

from trytond.model import ModelView, ModelSQL, fields
from trytond.pyson import Not, Equal, Eval, Bool
from trytond.transaction import Transaction
from trytond.pool import Pool
from decimal import Decimal

_ZERO = Decimal('0.0')

class Move(ModelSQL, ModelView):
    _name = 'stock.move'

    amount = fields.Function(fields.Numeric('Amount',
            digits=(16, 4),
            states={
                'invisible': Not(Bool(Eval('unit_price_required'))),
                'required': Bool(Eval('unit_price_required')),
                'readonly': Not(Equal(Eval('state'), 'draft')),
                }, on_change_with=['quantity', 'unit_price'],
            ),'get_amount')

    def get_amount(self, ids, name):
        currency_obj = Pool().get('currency.currency')
        res = {}
        for move in self.browse(ids):
            res[move.id] = _ZERO
            if move.quantity:
                res[move.id] += currency_obj.round(
                            move.company.currency,
                            Decimal(str(move.quantity)) * move.unit_price)
        return res

Move()

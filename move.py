#This file is part stock_valued module for Tryton.
#The COPYRIGHT file at the top level of this repository contains
#the full copyright notices and license terms.
from trytond.model import fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Equal, Eval, Not
from trytond.transaction import Transaction
from decimal import Decimal

__all__ = ['Move']
__metaclass__ = PoolMeta

_ZERO = Decimal('0.0')
STATES = {
    'invisible': Not(Equal(Eval('state', ''), 'done')),
    }


class Move:
    "Stock Move"
    __name__ = 'stock.move'

    currency_digits = fields.Function(fields.Integer('Currency Digits',
        on_change_with=['currency']), 'on_change_with_currency_digits')
    gross_unit_price = fields.Function(fields.Numeric('Gross Price',
            digits=(16, 4), states=STATES, depends=['state']),
        'get_amount')
    discount = fields.Function(fields.Numeric('Discount',
            digits=(16, 4), states=STATES, depends=['state']),
        'get_amount')
    tax_amount = fields.Function(fields.Numeric('Tax',
            digits=(16, Eval('currency_digits', 2)), states=STATES,
                depends=['currency_digits', 'state']),
        'get_amount')
    amount = fields.Function(fields.Numeric('Amount',
            digits=(16, Eval('currency_digits', 2)), states=STATES,
            depends=['currency_digits', 'state']),
        'get_amount')

    @staticmethod
    def default_currency_digits():
        Company = Pool().get('company.company')
        if Transaction().context.get('company'):
            company = Company(Transaction().context['company'])
            return company.currency.digits
        return 2

    def on_change_with_currency_digits(self, name=None):
        if self.currency:
            return self.currency.digits
        return 2

    @classmethod
    def get_amount(cls, moves, names):
        pool = Pool()
        Invoice = pool.get('account.invoice')
        Tax = pool.get('account.tax')
        try:
            PurchaseLine = pool.get('purchase.line')
        except:
            PurchaseLine = type(None)
        try:
            SaleLine = pool.get('sale.line')
        except:
            SaleLine = type(None)

        result = {}
        for fname in names:
            result[fname] = {}
        for move in moves:
            gross_unit_price = None
            discount = None
            tax_amount = None
            amount = _ZERO
            if move.quantity:
                if (move.origin and
                        isinstance(move.origin, (SaleLine, PurchaseLine))):
                    if hasattr(move.origin, 'gross_unit_price'):
                        gross_unit_price = (move.origin.gross_unit_price
                            or _ZERO)
                    if hasattr(move.origin, 'discount'):
                        discount = move.origin.discount or _ZERO
                    inv_type = (isinstance(move.origin, SaleLine)
                        and 'out_invoice' or 'in_invoice')
                    taxes = Tax.compute(move.origin.taxes, move.unit_price,
                        move.quantity)
                    tax_amount = _ZERO
                    for tax in taxes:
                        unused, val = Invoice._compute_tax(tax, inv_type)
                        tax_amount += val['amount']
                        amount += val['base'] + val['amount']
                else:
                    amount += Decimal(str(move.quantity)) * move.unit_price
            if 'gross_unit_price' in names:
                result['gross_unit_price'][move.id] = gross_unit_price
            if 'discount' in names:
                result['discount'][move.id] = discount
            if 'tax_amount' in names:
                result['tax_amount'][move.id] = tax_amount
            if 'amount' in names:
                result['amount'][move.id] = amount
        return result

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
            on_change_with=['currency']),
        'on_change_with_currency_digits')
    gross_unit_price = fields.Function(fields.Numeric('Gross Price',
            digits=(16, 4), states=STATES, depends=['state']),
        'get_amount')
    discount = fields.Function(fields.Numeric('Discount',
            digits=(16, 4), states=STATES, depends=['state']),
        'get_amount')
    untaxed_amount = fields.Function(fields.Numeric('Untax Amount',
            digits=(16, Eval('currency_digits', 2)), states=STATES,
            depends=['currency_digits', 'state']),
        'get_amount')
    tax_amount = fields.Function(fields.Numeric('Tax',
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

    def _taxes_amount(self):
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

        if (not self.unit_price or not self.origin or
                not isinstance(self.origin, (SaleLine, PurchaseLine))):
            return {}

        if isinstance(self.origin, SaleLine) and self.origin.quantity >= 0:
            inv_type = 'out_invoice'
        elif isinstance(self.origin, SaleLine):
            inv_type = 'out_credit_note'
        elif (isinstance(self.origin, PurchaseLine) and
                self.origin.quantity >= 0):
            inv_type = 'in_invoice'
        else:
            inv_type = 'in_credit_note'

        tax_list = Tax.compute(self.origin.taxes, self.unit_price,
            self.quantity)
        # Don't round on each line to handle rounding error
        taxes = {}
        for tax in tax_list:
            key, val = Invoice._compute_tax(tax, inv_type)
            taxes[key] = val['amount']
        return taxes

    @classmethod
    def get_amount(cls, moves, names):
        result = {}
        for fname in names:
            result[fname] = {}
        for move in moves:
            if 'gross_unit_price' in names:
                result['gross_unit_price'][move.id] = (move.origin and
                    hasattr(move.origin, 'gross_unit_price') and
                    move.origin.gross_unit_price or _ZERO)
            if 'discount' in names:
                result['discount'][move.id] = (move.origin and
                    hasattr(move.origin, 'discount') and
                    move.origin.gross_unit_price or _ZERO)
            if 'untaxed_amount' in names:
                result['untaxed_amount'][move.id] = (
                    Decimal(str(move.quantity or 0)) *
                    (move.unit_price or _ZERO))
            if 'tax_amount' in names:
                result['tax_amount'][move.id] = sum(
                    move._taxes_amount().values(), _ZERO)
        return result

# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from decimal import Decimal

from trytond.model import fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Equal, Eval, Not
from trytond.transaction import Transaction
from trytond.config import config as config_

__all__ = ['Move']
__metaclass__ = PoolMeta

_ZERO = Decimal('0.0')
STATES = {
    'invisible': Not(Equal(Eval('state', ''), 'done')),
    }
DIGITS = config_.getint('product', 'price_decimal', default=4)
DISCOUNT_DIGITS = config_.getint('product', 'discount_decimal', default=4)


class Move:
    __name__ = 'stock.move'

    currency_digits = fields.Function(fields.Integer('Currency Digits'),
        'on_change_with_currency_digits')
    gross_unit_price = fields.Function(fields.Numeric('Gross Price',
            digits=(16, DIGITS), states=STATES, depends=['state']),
        'get_origin_fields')
    discount = fields.Function(fields.Numeric('Discount',
            digits=(16, DISCOUNT_DIGITS), states=STATES, depends=['state']),
        'get_origin_fields')
    untaxed_amount = fields.Function(fields.Numeric('Untax Amount',
            digits=(16, Eval('currency_digits', 2)), states=STATES,
            depends=['currency_digits', 'state']),
        'get_origin_fields')
    taxes = fields.Function(fields.Many2Many('account.tax', None, None,
            'Taxes'),
        'get_origin_fields')
    tax_amount = fields.Function(fields.Numeric('Tax Amount',
            digits=(16, Eval('currency_digits', 2)), states=STATES,
            depends=['currency_digits', 'state']),
        'get_tax_amount')
    total_amount = fields.Function(fields.Numeric('Total Amount',
            digits=(16, Eval('currency_digits', 2)),
            depends=['currency_digits']),
        'get_total_amount')

    @classmethod
    def __setup__(cls):
        super(Move, cls).__setup__()
        unit_price_invisible = cls.unit_price.states.get('invisible')
        if unit_price_invisible:
            cls.unit_price.states['readonly'] = unit_price_invisible
            cls.unit_price.states['invisible'] = {}

    @staticmethod
    def default_currency_digits():
        Company = Pool().get('company.company')
        if Transaction().context.get('company'):
            company = Company(Transaction().context['company'])
            return company.currency.digits
        return 2

    @fields.depends('currency')
    def on_change_with_currency_digits(self, name=None):
        if self.currency:
            return self.currency.digits
        return 2

    def _taxes_amount(self):
        pool = Pool()
        try:
            PurchaseLine = pool.get('purchase.line')
        except:
            PurchaseLine = type(None)
        try:
            SaleLine = pool.get('sale.line')
        except:
            SaleLine = type(None)

        total_taxes = Decimal(0)
        if (not self.unit_price or not self.origin or
                not isinstance(self.origin, (SaleLine, PurchaseLine))):
            return total_taxes

        if isinstance(self.origin, SaleLine):
            sale = self.origin.sale
            line = self.origin
            sale.lines = [line]
            taxes = sale._get_taxes().itervalues()
            total_taxes = sum(tax['amount'] for tax in taxes)
            return total_taxes

        if isinstance(self.origin, PurchaseLine):
            purchase = self.origin.purchase
            line = self.origin
            purchase.lines = [line]
            taxes = purchase._get_taxes().itervalues()
            total_taxes = sum(tax['amount'] for tax in taxes)
            return total_taxes

        return total_taxes

    @classmethod
    def get_origin_fields(cls, moves, names):
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
                    move.origin.discount or _ZERO)
            if 'untaxed_amount' in names:
                result['untaxed_amount'][move.id] = (
                    Decimal(str(move.quantity or 0)) *
                    (move.unit_price or _ZERO))
            if 'taxes' in names:
                result['taxes'][move.id] = (move.origin and
                    hasattr(move.origin, 'taxes') and
                    [t.id for t in move.origin.taxes] or [])
        return result

    def get_total_amount(self, name):
        return self.untaxed_amount + self.tax_amount

    def get_tax_amount(self, name):
        return self._taxes_amount()

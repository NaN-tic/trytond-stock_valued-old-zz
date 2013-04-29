#This file is part stock_valued module for Tryton.
#The COPYRIGHT file at the top level of this repository contains 
#the full copyright notices and license terms.

from trytond.model import fields
from trytond.pyson import Eval
from trytond.transaction import Transaction
from trytond.pool import Pool, PoolMeta
from decimal import Decimal

__all__ = ['ShipmentOut']
__metaclass__ = PoolMeta

class ShipmentOut:
    __name__ = 'stock.shipment.out'
    currency = fields.Function(fields.Integer('Currency'),
        'on_change_with_currency')
    currency_digits = fields.Function(fields.Integer('Currency Digits'),
        'on_change_with_currency_digits')
    untaxed_amount = fields.Function(fields.Numeric('Untaxed',
            digits=(16, Eval('currency_digits', 2)),
            depends=['currency_digits']), 'get_untaxed_amount')
    untaxed_amount_cache = fields.Numeric('Untaxed Cache',
        digits=(16, Eval('currency_digits', 2)),
        readonly=True,
        depends=['currency_digits'])
    tax_amount = fields.Function(fields.Numeric('Tax',
            digits=(16, Eval('currency_digits', 2)),
            depends=['currency_digits']), 'get_tax_amount')
    tax_amount_cache = fields.Numeric('Tax Cache',
        digits=(16, Eval('currency_digits', 2)),
        readonly=True,
        depends=['currency_digits'])
    total_amount = fields.Function(fields.Numeric('Total',
            digits=(16, Eval('currency_digits', 2)),
            depends=['currency_digits']), 'get_total_amount')
    total_amount_cache = fields.Numeric('Total Tax',
        digits=(16, Eval('currency_digits', 2)),
        readonly=True,
        depends=['currency_digits'])

    @classmethod
    def __setup__(cls):
        super(ShipmentOut, cls).__setup__()
        cls._states_cached = ['done', 'assigned', 'packed', 'waiting', 'cancel']

    def on_change_with_currency(self, name=None):
        if self.company:
            return self.company.currency
        return None

    def on_change_with_currency_digits(self, name=None):
        if self.company:
            return self.company.currency.digits
        return 2

    def get_tax_context(self):
        context = {}
        user = Pool().get('res.user')(Transaction().user)
        context['language'] = user.language
        if self.customer and self.customer.lang:
            context['language'] = self.customer.lang.code
        return context

    def get_untaxed_amount(self, name):
        '''
        Compute the untaxed amount for each ShipmentOut
        '''
        Currency = Pool().get('currency.currency')
        if (self.state in self._states_cached
                and self.untaxed_amount_cache is not None):
            return self.untaxed_amount_cache
        amount = sum((m.amount for m in self.outgoing_moves), Decimal(0))
        return Currency.round(self.company.currency, amount)

    def get_tax_amount(self, name):
        '''
        Compute tax amount for each ShipmentOut
        '''
        pool = Pool()
        Currency = pool.get('currency.currency')
        Tax = pool.get('account.tax')
        Invoice = pool.get('account.invoice')

        if (self.state in self._states_cached
                and self.tax_amount_cache is not None):
            return self.tax_amount_cache
        context = self.get_tax_context()
        taxes = {}
        for move in self.outgoing_moves:
            with Transaction().set_context(context):
                tax_list = Tax.compute(getattr(move.product, 'customer_taxes', []),
                    move.unit_price or Decimal('0.0'),
                    move.quantity or 0.0)
            for tax in tax_list:
                key, val = Invoice._compute_tax(tax, 'out_invoice')
                if not key in taxes:
                    taxes[key] = val['amount']
                else:
                    taxes[key] += val['amount']
        amount = sum((Currency.round(self.company.currency, taxes[key])
                for key in taxes), Decimal(0))
        return Currency.round(self.company.currency, amount)

    def get_total_amount(self, name):
        '''
        Return the total amount of each ShipmentOut
        '''
        if (self.state in self._states_cached
                and self.total_amount_cache is not None):
            return self.total_amount_cache
        if self.currency:
            return self.currency.round(self.untaxed_amount + self.tax_amount)
        return Decimal(0)



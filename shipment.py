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
    untaxed_amount = fields.Numeric('Untaxed',
        digits=(16, Eval('currency_digits', 2)),
        readonly=True,
        depends=['currency_digits'])
    tax_amount = fields.Numeric('Tax',
        digits=(16, Eval('currency_digits', 2)),
        readonly=True,
        depends=['currency_digits'])
    total_amount = fields.Numeric('Total Tax',
        digits=(16, Eval('currency_digits', 2)),
        readonly=True,
        depends=['currency_digits'])

    def on_change_with_currency(self, name=None):
        if self.company:
            return self.company.currency
        return None

    def on_change_with_currency_digits(self, name=None):
        if self.company:
            return self.company.currency.digits
        return 2

    @classmethod
    def done(cls, shipments):
        super(ShipmentOut, cls).done(shipments)
        for shipment in shipments:
            data = {
                'untaxed_amount': shipment.get_untaxed_amount(None),
                'tax_amount': shipment.get_tax_amount(None),
                'total_amount': shipment.get_total_amount(None),
                }
            cls.write([shipment], data)

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

        context = self.get_tax_context()
        taxes = {}
        for move in self.outgoing_moves:
            with Transaction().set_context(context):
                tax_list = Tax.compute(getattr(move.product,
                        'customer_taxes_used', []),
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
        if self.currency:
            return self.currency.round((self.untaxed_amount or Decimal('0.0'))
                + (self.tax_amount or Decimal('0.0')))
        return Decimal(0)

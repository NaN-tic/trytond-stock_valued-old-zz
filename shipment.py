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
    currency = fields.Function(fields.Many2One('currency.currency', 'Currency',
            on_change_with=['company']),
        'on_change_with_currency')
    currency_digits = fields.Function(fields.Integer('Currency Digits',
            on_change_with=['company']),
        'on_change_with_currency_digits')
    untaxed_amount = fields.Numeric('Untaxed',
        digits=(16, Eval('currency_digits', 2)),
        readonly=True,
        depends=['currency_digits'])
    tax_amount = fields.Numeric('Tax',
        digits=(16, Eval('currency_digits', 2)),
        readonly=True,
        depends=['currency_digits'])
    total_amount = fields.Numeric('Total',
        digits=(16, Eval('currency_digits', 2)),
        readonly=True,
        depends=['currency_digits'])

    def on_change_with_currency(self, name=None):
        if self.company:
            return self.company.currency.id
        return None

    def on_change_with_currency_digits(self, name=None):
        if self.company:
            return self.company.currency.digits
        return 2

    @classmethod
    def done(cls, shipments):
        super(ShipmentOut, cls).done(shipments)
        for shipment in shipments:
            cls.write([shipment], shipment.calc_amounts())

    def calc_amounts(self):
        Currency = Pool().get('currency.currency')
        untaxed_amount = Decimal(0)
        taxes = {}
        for move in self.outgoing_moves:
            if move.state == 'cancelled':
                continue
            if move.currency and move.currency != self.company.currency:
                # convert wrt currency
                with Transaction().set_context(date=self.effective_date):
                    untaxed_amount += Currency.compute(move.currency,
                        move.untaxed_amount, self.company.currency,
                        round=False)
                    for key, value in move._taxes_amount().items():
                        value = Currency.compute(move.currency, value,
                            self.company.currency, round=False)
                        taxes[key] = taxes.get(key, Decimal(0)) + value
            else:
                untaxed_amount += move.untaxed_amount
                for key, value in move._taxes_amount().items():
                    taxes[key] = taxes.get(key, Decimal(0)) + value

        untaxed_amount = self.company.currency.round(untaxed_amount)
        tax_amount = sum((self.company.currency.round(tax)
                for tax in taxes.values()), Decimal(0))
        return {
            'untaxed_amount': untaxed_amount,
            'tax_amount': tax_amount,
            'total_amount': untaxed_amount + tax_amount,
            }

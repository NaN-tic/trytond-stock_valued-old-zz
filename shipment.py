# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from decimal import Decimal

from trytond.model import fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval
from trytond.transaction import Transaction

__all__ = ['ShipmentIn', 'ShipmentOut']
__metaclass__ = PoolMeta

MOVES = {
    'stock.shipment.in': 'incoming_moves',
    'stock.shipment.in.return': 'moves',
    'stock.shipment.out': 'outgoing_moves',
    'stock.shipment.out.return': 'incoming_moves',
    }


class ShipmentValuedMixin:
    currency = fields.Function(fields.Many2One('currency.currency',
            'Currency'),
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
    total_amount = fields.Numeric('Total',
        digits=(16, Eval('currency_digits', 2)),
        readonly=True,
        depends=['currency_digits'])
    untaxed_amount_func = fields.Function(fields.Numeric('Untaxed',
        digits=(16, Eval('currency_digits', 2)),
        depends=['currency_digits']), 'get_amounts')
    tax_amount_func = fields.Function(fields.Numeric('Tax',
        digits=(16, Eval('currency_digits', 2)),
        readonly=True,
        depends=['currency_digits']), 'get_amounts')
    total_amount_func = fields.Function(fields.Numeric('Total',
        digits=(16, Eval('currency_digits', 2)),
        readonly=True,
        depends=['currency_digits']), 'get_amounts')

    @fields.depends('company')
    def on_change_with_currency(self, name=None):
        if self.company:
            return self.company.currency.id
        return None

    @fields.depends('company')
    def on_change_with_currency_digits(self, name=None):
        if self.company:
            return self.company.currency.digits
        return 2

    def calc_amounts(self):
        pool = Pool()
        Currency = pool.get('currency.currency')
        Date = pool.get('ir.date')

        untaxed_amount = Decimal(0)
        tax_amount = Decimal(0)
        for move in getattr(self, MOVES.get(self.__name__)):
            if move.state == 'cancelled':
                continue
            if move.currency and move.currency != self.company.currency:
                # convert wrt currency
                date = self.effective_date or Date.today()
                with Transaction().set_context(date=date):
                    untaxed_amount += Currency.compute(move.currency,
                        move.untaxed_amount, self.company.currency,
                        round=False)
                    tax_amount += Currency.compute(move.currency,
                        move.tax_amount, self.company.currency,
                        round=False)
            else:
                untaxed_amount += move.untaxed_amount
                tax_amount += move.tax_amount

        untaxed_amount = self.company.currency.round(untaxed_amount)
        tax_amount = self.company.currency.round(tax_amount)

        return {
            'untaxed_amount': untaxed_amount,
            'tax_amount': tax_amount,
            'total_amount': untaxed_amount + tax_amount,
            }

    @classmethod
    def get_amounts(cls, shipments, names):
        untaxed_amount = dict((i.id, Decimal(0)) for i in shipments)
        tax_amount = dict((i.id, Decimal(0)) for i in shipments)
        total_amount = dict((i.id, Decimal(0)) for i in shipments)

        for shipment in shipments:
            if shipment.untaxed_amount:
                untaxed_amount[shipment.id] = shipment.untaxed_amount
                tax_amount[shipment.id] = shipment.tax_amount
                total_amount[shipment.id] = shipment.total_amount
            else:
                res = shipment.calc_amounts()
                untaxed_amount[shipment.id] = res['untaxed_amount']
                tax_amount[shipment.id] = res['tax_amount']
                total_amount[shipment.id] = res['total_amount']
        result = {
            'untaxed_amount_func': untaxed_amount,
            'tax_amount_func': tax_amount,
            'total_amount_func': total_amount,
            }
        for key in result.keys():
            if key not in names:
                del result[key]
        return result


class ShipmentIn(ShipmentValuedMixin):
    __name__ = 'stock.shipment.in'

    @classmethod
    def create(cls, shipments):
        shipments = super(ShipmentIn, cls).create(shipments)
        for shipment in shipments:
            cls.write([shipment], shipment.calc_amounts())
        return shipments

    @classmethod
    def receive(cls, shipments):
        super(ShipmentIn, cls).receive(shipments)
        for shipment in shipments:
            cls.write([shipment], shipment.calc_amounts())

    @classmethod
    def done(cls, shipments):
        super(ShipmentIn, cls).done(shipments)
        for shipment in shipments:
            cls.write([shipment], shipment.calc_amounts())


class ShipmentOut(ShipmentValuedMixin):
    __name__ = 'stock.shipment.out'

    @classmethod
    def wait(cls, shipments):
        super(ShipmentOut, cls).wait(shipments)
        for shipment in shipments:
            cls.write([shipment], shipment.calc_amounts())

    @classmethod
    def assign(cls, shipments):
        super(ShipmentOut, cls).assign(shipments)
        for shipment in shipments:
            cls.write([shipment], shipment.calc_amounts())

    @classmethod
    def pack(cls, shipments):
        super(ShipmentOut, cls).pack(shipments)
        for shipment in shipments:
            cls.write([shipment], shipment.calc_amounts())

    @classmethod
    def done(cls, shipments):
        super(ShipmentOut, cls).done(shipments)
        for shipment in shipments:
            cls.write([shipment], shipment.calc_amounts())

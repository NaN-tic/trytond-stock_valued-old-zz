#This file is part stock_valued module for Tryton.
#The COPYRIGHT file at the top level of this repository contains 
#the full copyright notices and license terms.

from trytond.model import ModelView, ModelSQL, fields
from trytond.pyson import Eval
from trytond.transaction import Transaction
from trytond.pool import Pool
from decimal import Decimal

class ShipmentOut(ModelSQL, ModelView):
    _name = 'stock.shipment.out'

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

    def __init__(self):
        super(ShipmentOut, self).__init__()
        self._states_cached = ['done', 'assigned', 'packed', 'waiting', 'cancel']

    def get_tax_context(self, shipment):
        party_obj = Pool().get('party.party')
        res = {}
        if isinstance(shipment, dict):
            if shipment.get('customer'):
                party = party_obj.browse(shipment['customer'])
                if party.lang:
                    res['language'] = party.lang.code
        else:
            if shipment.customer.lang:
                res['language'] = shipment.customer.lang.code
        return res

    def get_untaxed_amount(self, ids, name):
        '''
        Compute the untaxed amount for each ShipmentOut
        '''
        currency_obj = Pool().get('currency.currency')
        amounts = {}
        for shipment in self.browse(ids):
            if (shipment.state in self._states_cached
                    and shipment.untaxed_amount_cache is not None):
                amounts[shipment.id] = shipment.untaxed_amount_cache
                continue
            amount = sum((m.amount for m in shipment.outgoing_moves), Decimal(0))
            amounts[shipment.id] = currency_obj.round(shipment.company.currency, amount)
        return amounts

    def get_tax_amount(self, ids, name):
        '''
        Compute tax amount for each ShipmentOut
        '''
        pool = Pool()
        currency_obj = pool.get('currency.currency')
        tax_obj = pool.get('account.tax')
        invoice_obj = pool.get('account.invoice')

        amounts = {}
        for shipment in self.browse(ids):
            if (shipment.state in self._states_cached
                    and shipment.tax_amount_cache is not None):
                amounts[shipment.id] = shipment.tax_amount_cache
                continue
            context = self.get_tax_context(shipment)
            taxes = {}
            for move in shipment.outgoing_moves:
                with Transaction().set_context(context):
                    tax_list = tax_obj.compute(
                            [t.id for t in move.product.customer_taxes], 
                            move.unit_price, move.quantity)
                # Don't round on each line to handle rounding error
                for tax in tax_list:
                    key, val = invoice_obj._compute_tax(tax, 'out_invoice')
                    if not key in taxes:
                        taxes[key] = val['amount']
                    else:
                        taxes[key] += val['amount']
            amount = sum((currency_obj.round(shipment.company.currency, taxes[key])
                    for key in taxes), Decimal(0))
            amounts[shipment.id] = currency_obj.round(shipment.company.currency, amount)
        return amounts

    def get_total_amount(self, ids, name):
        '''
        Return the total amount of each ShipmentOut
        '''
        currency_obj = Pool().get('currency.currency')
        amounts = {}
        for shipment in self.browse(ids):
            if (shipment.state in self._states_cached
                    and shipment.total_amount_cache is not None):
                amounts[shipment.id] = shipment.total_amount_cache
                continue
            amounts[shipment.id] = currency_obj.round(shipment.company.currency,
                shipment.untaxed_amount + shipment.tax_amount)
        return amounts

ShipmentOut()

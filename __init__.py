#This file is part stock_valued module for Tryton.
#The COPYRIGHT file at the top level of this repository contains 
#the full copyright notices and license terms.
from trytond.pool import Pool
from .move import *
from .shipment import *


def register():
    Pool.register(
        Move,
        ShipmentOut,
        module='stock_valued', type_='model')

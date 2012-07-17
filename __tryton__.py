#This file is part of Tryton.  The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
{
    'name': 'Stock Valued',
    'name_ca_ES': 'Albarans valorats',
    'name_es_ES': 'Albaranes valorados',
    'version': '2.4.0',
    'author': 'Zikzakmedia',
    'email': 'zikzak@zikzakmedia.com',
    'website': 'http://www.zikzakmedia.com/',
    'description': '''Add amount untaxed, tax and total in Shipment Out.
If you have installed sale_discount, remember install stock_valued_discount
    ''',
    'description_ca_ES': '''Afegeix base, taxes i total en els albarans.
Si heu instal·lat el mòdul sale_discount, recordeu d'instal·lar també stock_valued_discount
    ''',
    'description_es_ES': '''Añade base, impuestos y total en los albaranes
Si habeis instalado el módulo sale_discount, recuerden también de instalar stock_valued_discount
    ''',
    'depends': [
        'ir',
        'res',
        'stock',
    ],
    'xml': [
        'stock.xml',
        'move.xml',
        'shipment.xml',
    ],
    'translation': [
        'locale/ca_ES.po',
        'locale/es_ES.po',
    ]
}

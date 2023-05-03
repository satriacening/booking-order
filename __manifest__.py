# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'booking_order_satria_27042023',
    'version': '1.1',
    'category': 'Sales',
    'sequence': 1,
    'summary': 'Booking Order',
    'description': """
        Test Module Booking order
        Satria Putra
        27 April 2023
    """,
    'depends': [
        'note',
        'sale',
        'base_setup',
        'mail',
        'resource',
        'web_kanban',
    ],
    'data': [
        'wizard/cancel_reason_view.xml',
        'security/ir.model.access.csv',
        'views/booking_view.xml',
        'views/cancel_view.xml',
        'report/report.xml',
        'data/ir_sequence_data.xml',
        'report/report_templates.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'qweb': [],
}

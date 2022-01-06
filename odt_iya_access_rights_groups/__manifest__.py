# -*- coding: utf-8 -*-
{
    'name': "IYA Groups",

    'description': """
        access rights groups for iya company
    """,

    'author': "Odootec",
    'website': "http://www.odootec.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Base',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','product'
                ],

    # always loaded
    'data': [
        'views/group_views.xml',
    ]
}

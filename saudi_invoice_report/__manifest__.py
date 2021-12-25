# -*- coding: utf-8 -*-
{
    'name': "Saudi Invoice Report",

    'summary': """
        Saudi Invoice Report""",

    'description': """
        Saudi Invoice Report
    """,

    'author': "erp-bank",
    'website': "www.erp-bank.com",

    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','account','account_accountant','web','sa_uae_vat','l10n_sa_invoice'],

    # always loaded
    'data': [
        'views/res_company_view.xml',
        'views/saudi_report_layout.xml',
        'views/vat_invoice_view.xml',
        'views/saudi_invoice_report.xml',
        'data/mail_template_data.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}

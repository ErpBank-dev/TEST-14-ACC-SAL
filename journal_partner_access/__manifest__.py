# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Journal & Partner Access',
    'version': '14.0.0.0',
    'summary': 'Journal & Partner Access',
    "description": """
            Journal & Partner Access
           """,
    'author': "erp-bank",
    'website': "www.erp-bank.com",
    'depends': ['base','account','sale'],
    'data': [
        'security/security.xml',
        'views/account_journal_view.xml',
    ],

    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
}


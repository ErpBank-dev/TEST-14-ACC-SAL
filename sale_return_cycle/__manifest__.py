{
    'name': 'Sale Return',
    'version': '12.0.1.0.0',
    'category': 'Sale',
    'license': 'AGPL-3',
    'author': 'Mostafa Mohamed',
    'summary': 'Sale and Return in the same cycle',
    'depends': [
        'sale',
        'account'
    ],
    'data': [
        'report/sale_report_return_view.xml',
        'security/ir.model.access.csv',
        'views/account_move_view.xml',
        'views/sale_order_view.xml',
        # 'views/stock_move_view.xml',

    ],
    'installable': True,
    'auto_install': False,
}

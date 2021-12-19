{
    'name': "Access Right for Settings",

    'summary': "Special Access right for settings of Sales,Purchase,Stock and Accounting",
    'author': "odootec",
    'category': 'Tools',
    'version': '0.1',

    'depends': ['sale', 'purchase', 'account', 'stock', 'mrp'],

    'data': [
        'security/settings_group.xml',
        'views/configuration_view.xml'
    ],

}

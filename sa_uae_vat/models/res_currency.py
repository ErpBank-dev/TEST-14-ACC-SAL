# -*- coding: utf-8 -*-
# Copyright (C) 2017-Today  Technaureus Info Solutions(<http://technaureus.com/>).
from odoo import api, fields, models


class ResCurrency(models.Model):
    _inherit = 'res.currency'

    currency_unit_label = fields.Char(string="Currency Unit", help="Currency Unit Name", translate="True")
    currency_subunit_label = fields.Char(string="Currency Subunit", help="Currency Subunit Name", translate="True")
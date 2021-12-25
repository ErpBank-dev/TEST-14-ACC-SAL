# -*- coding: utf-8 -*-
# Copyright (C) 2017-Today  Technaureus Info Solutions(<http://technaureus.com/>).
from odoo import api, fields, models


class Company(models.Model):
    _inherit = 'res.company'

    name_arabic = fields.Char(string="Company Arabic Name")
    street_arabic = fields.Char("Street in Arabic")
    street2_arabic = fields.Char("Street2 in Arabic")
    zip_arabic = fields.Char("ZIP in Arabic")
    city_arabic = fields.Char("City in Arabic")
    state_arabic = fields.Char(string="State Arabic Name")
    country_arabic = fields.Char(string="Country Name Arabic")
    tin_label = fields.Selection([('trn', 'TRN'), ('vat_reg_no', 'VAT Reg. No.')],
                                 required=True, default='trn', string="TIN Label");
    invoice_header_label = fields.Selection([('vat', 'VAT INVOICE'), ('tax', 'TAX INVOICE')], required=True,
                                            default='vat', string="Invoice Header Label")
    vat_accounting = fields.Selection([('uae', 'UAE'), ('sa', 'Saudi Arabia')], default='sa', required=True,
                                      string="VAT Accounting for")
    place_supply = fields.Selection(
        [('abu_dhabi', 'Abu Dhabi'), ('ajman', 'Ajman'), ('dubai', 'Dubai'), ('fujairah', 'Fujairah'),
         ('ras_al_khaimah', 'Ras al-Khaimah'), ('sharjah', 'Sharjah'), ('umm_al_quwain', 'Umm al-Quwain')],
        string="Place of Supply")

    @api.onchange('state_id')
    def onchangeState(self):
        if (self.state_id.arabic_name):
            self.state_arabic = self.state_id.arabic_name
        else:
            self.state_arabic = ""
        for state in self.state_id:
            if (state.country_id.arabic_name):
                self.country_arabic = state.country_id.arabic_name
            else:
                self.country_arabic = ""

    @api.onchange('country_id')
    def onchangeCountry(self):
        if (self.country_id.arabic_name):
            self.country_arabic = self.country_id.arabic_name
        else:
            self.country_arabic = ""


class State(models.Model):
    _inherit = 'res.country.state'

    arabic_name = fields.Char(string="State Arabic Name")


class Country(models.Model):
    _inherit = 'res.country'

    arabic_name = fields.Char(string="Country Arabic Name")

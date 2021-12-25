# -*- coding: utf-8 -*-
# Copyright (C) 2017-Today  Technaureus Info Solutions(<http://technaureus.com/>).
from odoo import api, fields, models

class Partner(models.Model):
    _inherit = 'res.partner'
    
    partner_place_supply = fields.Selection([('abu_dhabi','Abu Dhabi'), ('ajman','Ajman'), ('dubai','Dubai'), ('fujairah','Fujairah'),
                     ('ras_al_khaimah','Ras al-Khaimah'), ('sharjah','Sharjah'), ('umm_al_quwain','Umm al-Quwain')], string= "Place of Supply")
    partner_vat_accounting = fields.Selection(related='company_id.vat_accounting')
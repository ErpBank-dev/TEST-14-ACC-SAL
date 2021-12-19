# -*- coding: utf-8 -*-
from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    return_invoice_id = fields.Many2one(comodel_name='account.move', string='Credit Note')
    def action_post(self):
        res = super(AccountMove, self).action_post()
        if self.return_invoice_id:
            self.return_invoice_id.sudo().action_post()
        return res


AccountMove()

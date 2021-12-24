# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError



class AccountJournal(models.Model):
    _inherit = 'account.journal'
    user_ids=fields.Many2many('res.users')



class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'
    user_id = fields.Many2one('res.users', 'Responsible', default=lambda self: self.env.user)


    @api.depends('company_id', 'source_currency_id','user_id')
    def _compute_journal_id(self):
        for wizard in self:
            domain = [
                ('type', 'in', ('bank', 'cash')),
                ('company_id', '=', wizard.company_id.id),
                ('user_ids', 'in',[wizard.user_id.id]),
            ]
            journal = None
            if wizard.source_currency_id:
                journal = self.env['account.journal'].search(domain + [('currency_id', '=', wizard.source_currency_id.id)], limit=1)
            if not journal:
                journal = self.env['account.journal'].search(domain, limit=1)
            wizard.journal_id = journal


class AccountMove(models.Model):
    _inherit = 'account.move'

    partner_filter_domain = fields.Many2many('res.partner',compute='_compute_partner_filter_domain')

    @api.depends('move_type')
    def _compute_partner_filter_domain(self):
        for move in self:
            if move.move_type in ['out_invoice','out_refund','out_receipt']:
                move.update({'partner_filter_domain':[(6,0,self.env['res.partner'].search([('customer_rank' ,'>', 0)]).ids)]})
            elif move.move_type in ['in_invoice','in_refund','in_receipt']:
                move.update({'partner_filter_domain':[(6,0,self.env['res.partner'].search([('supplier_rank', '>', 0)]).ids)]})
            else:
                move.update({'partner_filter_domain':[(6,0,self.env['res.partner'].search([]).ids)]})

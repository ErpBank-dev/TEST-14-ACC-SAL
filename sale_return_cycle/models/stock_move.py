# -*- coding: utf-8 -*-
from odoo import fields, models


class StockMove(models.Model):
    _inherit = 'stock.move'
    sale_return_line_id = fields.Many2one('sale.order.line',
                                          'Sale Order Line', ondelete='set null', index=True, readonly=True)
    created_return_sale_line_id = fields.Many2one('sale.order.line',
                                                  'Created Sale Order Line', ondelete='set null', readonly=True,
                                                  copy=False)

    def _clean_merged(self):
        super(StockMove, self)._clean_merged()
        self.write({'created_return_sale_line_id': False})

    def _action_done(self):
        res = super(StockMove, self)._action_done()
        self.mapped('sale_return_line_id').sudo()._update_received_qty()
        return res

    def write(self, vals):
        res = super(StockMove, self).write(vals)
        if 'product_uom_qty' in vals:
            self.filtered(lambda m: m.state == 'done' and m.purchase_line_id).mapped(
                'sale_return_line_id').sudo()._update_received_qty()
        return res


StockMove()

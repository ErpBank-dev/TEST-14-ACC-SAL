# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from odoo.tools import float_is_zero, float_compare
from odoo.tools.translate import _

READONLY_STATES = {
    'sale': [('readonly', True)],
    'done': [('readonly', True)],
    'cancel': [('readonly', True)],
}


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # @api.model
    # def _default_return_picking_type(self):
    #     type_obj = self.env['stock.picking.type']
    #     company_id = self.env.context.get('company_id') or self.env.user.company_id.id
    #     types = type_obj.search([('code', '=', 'incoming'), ('warehouse_id.company_id', '=', company_id)])
    #     if not types:
    #         types = type_obj.search([('code', '=', 'incoming'), ('warehouse_id', '=', False)])
    #     return types[:1]
    #
    # return_picking_type_id = fields.Many2one('stock.picking.type', 'Return To', states=READONLY_STATES,
    #                                          required=True, default=_default_return_picking_type,
    #                                          help="This will determine operation type of Returned Products")
    # picking_count = fields.Integer(compute='_compute_return_picking', string='Picking count', default=0, store=True)
    # return_picking_ids = fields.Many2many('stock.picking', compute='_compute_return_picking', string='Receptions',
    #                                       copy=False,
    #                                       store=True)
    #
    #
    def _prepare_invoice(self):
        res = super(SaleOrder, self)._prepare_invoice()
        if self._context.get('negative'):
            res.update({'move_type': 'out_refund'})
        return res

    
    def action_negative_invoice_create(self, grouped=False, final=False):
        inv_obj = self.env['account.move']
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        invoices = {}
        references = {}
        invoices_origin = {}
        invoices_name = {}
        invoices_lines=[]

        for order in self:
            group_key = order.id if grouped else (order.partner_invoice_id.id, order.currency_id.id)
            pending_section = None

            for line in order.order_line.filtered(lambda item: item.product_uom_qty < 0):
                if line.display_type == 'line_section':
                    pending_section = line
                    continue
                if float_is_zero(line.qty_to_invoice, precision_digits=precision):
                    continue
                if group_key not in invoices:
                    inv_data = order.with_context(negative=True)._prepare_invoice()
                    invoice = inv_obj.sudo().create(inv_data)
                    references[invoice] = order
                    invoices[group_key] = invoice
                    invoices_origin[group_key] = [invoice.invoice_origin]
                    invoices_name[group_key] = [invoice.name]
                elif group_key in invoices:
                    if order.name not in invoices_origin[group_key]:
                        invoices_origin[group_key].append(order.name)
                    if order.client_order_ref and order.client_order_ref not in invoices_name[group_key]:
                        invoices_name[group_key].append(order.client_order_ref)

                if line.qty_to_invoice > 0 or (line.qty_to_invoice < 0 and final):
                    if pending_section:
                        pending_section.invoice_line_create(invoices[group_key].id, pending_section.qty_to_invoice )
                        pending_section = None
                    invoices_lines.append(line._prepare_invoice_line())

            if references.get(invoices.get(group_key)):
                if order not in references[invoices[group_key]]:
                    references[invoices[group_key]] |= order

        for group_key in invoices:
            invoices[group_key].write({'name': ', '.join(invoices_name[group_key]),
                                       'invoice_origin': ', '.join(invoices_origin[group_key]),
                                       'invoice_line_ids': [(0, 0, inv) for inv in invoices_lines]})
            sale_orders = references[invoices[group_key]]
            if len(sale_orders) == 1:
                invoices[group_key].ref = sale_orders.reference
        if not invoices:

            raise UserError(_(
                'There is no invoiceable line. If a product has a Delivered quantities invoicing policy, please make sure that a quantity has been delivered.'))

        for invoice in invoices.values():

            # invoice.compute_taxes()
            if not invoice.invoice_line_ids:
                raise UserError(_(
                    'There is no invoiceable line. If a product has a Delivered quantities invoicing policy, please make sure that a quantity has been delivered.'))
            # If invoice is negative, do a refund invoice instead
            if invoice.amount_total < 0:
                invoice.move_type = 'out_invoice'
                for line in invoice.invoice_line_ids:
                    line.quantity = -line.quantity
            # Use additional field helper function (for account extensions)
            # for line in invoice.invoice_line_ids:
            #     line._set_additional_fields(invoice)
            # Necessary to force computation of taxes. In account_invoice, they are triggered
            # by onchanges, which are not triggered when doing a create.
            # invoice.compute_taxes()
            # Idem for partner
            so_payment_term_id = invoice.invoice_payment_term_id.id
            invoice._onchange_partner_id()
            # To keep the payment terms set on the SO
            invoice.invoice_payment_term_id = so_payment_term_id
            invoice.message_post_with_view('mail.message_origin_link',
                                           values={'self': invoice, 'invoice_origin': references[invoice]},
                                           subtype_id=self.env.ref('mail.mt_note').id)

        return [inv.id for inv in invoices.values()]

    
    def action_invoice_create(self, grouped=False, final=False):

        inv_obj = self.env['account.move']
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        invoices = {}
        references = {}
        invoices_origin = {}
        invoices_name = {}
        invoices_lines = []

        for order in self:
            group_key = order.id if grouped else (order.partner_invoice_id.id, order.currency_id.id)

            pending_section = None

            for line in order.order_line.filtered(lambda item: item.product_uom_qty > 0):
                if line.display_type == 'line_section':
                    pending_section = line
                    continue
                if float_is_zero(line.qty_to_invoice, precision_digits=precision):
                    continue
                if group_key not in invoices:
                    inv_data = order._prepare_invoice()
                    invoice = inv_obj.sudo().create(inv_data)
                    references[invoice] = order
                    invoices[group_key] = invoice
                    invoices_origin[group_key] = [invoice.invoice_origin]
                    invoices_name[group_key] = [invoice.name]
                elif group_key in invoices:
                    if order.name not in invoices_origin[group_key]:
                        invoices_origin[group_key].append(order.name)
                    if order.client_order_ref and order.client_order_ref not in invoices_name[group_key]:
                        invoices_name[group_key].append(order.client_order_ref)

                if line.qty_to_invoice > 0 or (line.qty_to_invoice < 0 and final):
                    if pending_section:
                        pending_section.invoice_line_create(invoices[group_key].id, pending_section.qty_to_invoice)
                        pending_section = None
                    invoices_lines.append(line._prepare_invoice_line())


            if references.get(invoices.get(group_key)):
                if order not in references[invoices[group_key]]:
                    references[invoices[group_key]] |= order

        for group_key in invoices:
            invoices[group_key].write({'name': ', '.join(invoices_name[group_key]),
                                       'invoice_origin': ', '.join(invoices_origin[group_key]),'invoice_line_ids':[(0, 0,inv)for inv in invoices_lines]})


            sale_orders = references[invoices[group_key]]
            if len(sale_orders) == 1:
                invoices[group_key].ref= sale_orders.reference

        if not invoices:
            raise UserError(_(
                'There is no invoiceable line. If a product has a Delivered quantities invoicing policy, please make sure that a quantity has been delivered.'))

        for invoice in invoices.values():
            # invoice.compute_taxes()

            if not invoice.invoice_line_ids:
                raise UserError(_(
                    'There is no invoiceable line. If a product has a Delivered quantities invoicing policy, please make sure that a quantity has been delivered.'))
            # If invoice is negative, do a refund invoice instead
            if invoice.amount_total < 0:
                invoice.move_type = 'out_refund'
                for line in invoice.invoice_line_ids:
                    line.quantity = -line.quantity
            # Use additional field helper function (for account extensions)
            # for line in invoice.invoice_line_ids:
            #     line._set_additional_fields(invoice)
            # Necessary to force computation of taxes. In account_invoice, they are triggered
            # by onchanges, which are not triggered when doing a create.
            # invoice.compute_taxes()
            # Idem for partner
            so_payment_term_id = invoice.invoice_payment_term_id.id
            invoice._onchange_partner_id()
            # To keep the payment terms set on the SO
            invoice.invoice_payment_term_id = so_payment_term_id
            invoice.message_post_with_view('mail.message_origin_link',
                                           values={'self': invoice, 'invoice_origin': references[invoice]},
                                           subtype_id=self.env.ref('mail.mt_note').id)
        positive_invoices = [inv.id for inv in invoices.values()]
        if self.order_line.filtered(lambda item: item.product_uom_qty < 0):
            negative_invoices = self.action_negative_invoice_create(grouped=False, final=False)
            if len(negative_invoices) == len(positive_invoices) == 1:
                self.env['account.move'].sudo().browse(positive_invoices).write(
                    {'return_invoice_id': negative_invoices[0]})
            # for record_data in self.env['account.move'].browse(negative_invoices):
                # record_data.action_invoice_open()
            positive_invoices.extend(negative_invoices)
        return positive_invoices

    # @api.depends('order_line.return_move_ids.returned_move_ids',
    #              'order_line.return_move_ids.state',
    #              'order_line.return_move_ids.picking_id')
    # def _compute_return_picking(self):
    #     for order in self:
    #         pickings = self.env['stock.picking']
    #         for line in order.order_line:
    #             moves = line.return_move_ids | line.return_move_ids.mapped('returned_move_ids')
    #             pickings |= moves.mapped('picking_id')
    #         order.return_picking_ids = pickings
    #         order.picking_count = len(pickings)
    #
    # return_group_id = fields.Many2one('procurement.group', string="Procurement Group", copy=False)
    #
    #
    # def action_view_receipt(self):
    #     action = self.env.ref('stock.action_picking_tree_all')
    #     result = action.read()[0]
    #     result['context'] = {}
    #     pick_ids = self.mapped('return_picking_ids')
    #     if not pick_ids or len(pick_ids) > 1:
    #         result['domain'] = "[('id','in',%s)]" % (pick_ids.ids)
    #     elif len(pick_ids) == 1:
    #         res = self.env.ref('stock.view_picking_form', False)
    #         result['views'] = [(res and res.id or False, 'form')]
    #         result['res_id'] = pick_ids.id
    #     return result
    #
    # def write(self, vals):
    #     if vals.get('order_line') and self.state == 'sale':
    #         for order in self:
    #             pre_order_line_qty = {order_line: order_line.product_uom_qty for order_line in
    #                                   order.mapped('order_line') if
    #                                   order_line.product_uom_qty < 0}
    #     res = super(SaleOrder, self).write(vals)
    #     if vals.get('order_line') and self.state == 'sale':
    #         for order in self:
    #             to_log = {}
    #             for order_line in order.order_line:
    #                 if pre_order_line_qty.get(order_line, False) and float_compare(pre_order_line_qty[order_line],
    #                                                                                order_line.product_uom_qty,
    #                                                                                precision_rounding=order_line.product_uom.rounding) > 0:
    #                     to_log[order_line] = (order_line.product_uom_qty, pre_order_line_qty[order_line])
    #             if to_log:
    #                 order._log_decrease_ordered_quantity(to_log)
    #     return res
    #
    # @api.depends('return_picking_ids')
    # def _compute_picking_receipt_ids(self):
    #     for order in self:
    #         order.picking_count = len(order.return_picking_ids)
    #
    # @api.model
    # def _prepare_picking(self):
    #     if not self.return_group_id:
    #         self.return_group_id = self.return_group_id.create({
    #             'name': self.name,
    #             'partner_id': self.partner_id.id
    #         })
    #     if not self.partner_id.property_stock_customer.id:
    #         raise UserError(_("You must set a Customer Location for this partner %s") % self.partner_id.name)
    #     return {
    #         'picking_type_id': self.return_picking_type_id.id,
    #         'partner_id': self.partner_id.id,
    #         'date': self.date_order,
    #         'origin': self.name,
    #         'location_dest_id': self._get_destination_location(),
    #         'location_id': self.partner_id.property_stock_customer.id,
    #         'company_id': self.company_id.id,
    #     }
    #
    #
    # def process_delivery(self):
    #     pick_to_backorder = self.env['stock.picking']
    #     pick_to_do = self.env['stock.picking']
    #     for picking in self.picking_ids:
    #         # If still in draft => confirm and assign
    #         if picking.state == 'draft':
    #             picking.action_confirm()
    #             if picking.state != 'assigned':
    #                 picking.action_assign()
    #                 if picking.state != 'assigned':
    #                     raise UserError(_("Could not reserve all requested products. Please use the \'Mark as Todo\' button to handle the reservation manually."))
    #         for move in picking.move_lines:
    #             for move_line in move.move_line_ids:
    #                 move_line.qty_done = move_line.product_uom_qty
    #         if picking._check_backorder():
    #             pick_to_backorder |= picking
    #             continue
    #         pick_to_do |= picking
    #     # Process every picking that do not require a backorder, then return a single backorder wizard for every other ones.
    #     if pick_to_do:
    #         pick_to_do.action_done()
    #     if pick_to_backorder:
    #         return pick_to_backorder._action_generate_backorder_wizard()
    #     return False
    #
    #
    # def process_receipt(self):
    #     pick_to_backorder = self.env['stock.picking']
    #     pick_to_do = self.env['stock.picking']
    #     for picking in self.return_picking_ids:
    #         # If still in draft => confirm and assign
    #         if picking.state == 'draft':
    #             picking.action_confirm()
    #             if picking.state != 'assigned':
    #                 picking.action_assign()
    #                 if picking.state != 'assigned':
    #                     raise UserError(_("Could not reserve all requested products. Please use the \'Mark as Todo\' button to handle the reservation manually."))
    #         for move in picking.move_lines:
    #             for move_line in move.move_line_ids:
    #                 move_line.qty_done = move_line.product_uom_qty
    #         if picking._check_backorder():
    #             pick_to_backorder |= picking
    #             continue
    #         pick_to_do |= picking
    #     # Process every picking that do not require a backorder, then return a single backorder wizard for every other ones.
    #     if pick_to_do:
    #         pick_to_do.action_done()
    #     if pick_to_backorder:
    #         return pick_to_backorder._action_generate_backorder_wizard()
    #     return False
    #
    #
    
    def action_view_invoice(self):
        invoices = self.mapped('invoice_ids').filtered(lambda inv:inv.move_type=='out_invoice')
        action = self.env.ref('account.action_move_out_invoice_type').read()[0]
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            action['views'] = [(self.env.ref('account.view_move_form').id, 'form')]
            action['res_id'] = invoices.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}

        return action


    
    def action_confirm(self):
        super(SaleOrder, self).action_confirm()
        # self._create_picking()
        # self.process_receipt()
        # self.process_delivery()
        self.action_invoice_create(final=True)
        return self.action_view_invoice()

    
    # def _create_picking(self):
    #     StockPicking = self.env['stock.picking']
    #     for order in self:
    #         if any([ptype in ['product', 'consu'] for ptype in order.order_line.mapped('product_id.type')]):
    #             pickings = order.return_picking_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
    #             if not pickings:
    #                 res = order._prepare_picking()
    #                 picking = StockPicking.create(res)
    #             else:
    #                 picking = pickings[0]
    #             moves = order.order_line.filtered(lambda x: x.product_uom_qty < 0)._create_stock_moves(picking)
    #             moves = moves.filtered(lambda x: x.state not in ('done', 'cancel'))._action_confirm()
    #             seq = 0
    #             for move in sorted(moves, key=lambda move: move.date_expected):
    #                 seq += 5
    #                 move.sequence = seq
    #             moves._action_assign()
    #             picking.message_post_with_view('mail.message_origin_link',
    #                                            values={'self': picking, 'origin': order},
    #                                            subtype_id=self.env.ref('mail.mt_note').id)
    #     return True
    #
    #
    # def action_cancel(self):
    #     for order in self:
    #         for pick in order.return_picking_ids:
    #             if pick.state == 'done':
    #                 raise UserError(
    #                     _('Unable to cancel purchase order %s as some receptions have already been done.') % (
    #                         order.name))
    #
    #         if order.state in ('draft', 'sent', 'to approve'):
    #             for order_line in order.order_line:
    #                 if order_line.return_move_dest_ids:
    #                     return_move_dest_ids = order_line.return_move_dest_ids.filtered(
    #                         lambda m: m.state not in ('done', 'cancel'))
    #                     siblings_states = (return_move_dest_ids.mapped('move_orig_ids')).mapped('state')
    #                     if all(state in ('done', 'cancel') for state in siblings_states):
    #                         return_move_dest_ids.write({'procure_method': 'make_to_stock'})
    #                         return_move_dest_ids._recompute_state()
    #
    #         for pick in order.return_picking_ids.filtered(lambda r: r.state != 'cancel'):
    #             pick.action_cancel()
    #
    #         order.order_line.write({'return_move_dest_ids': [(5, 0, 0)]})
    #
    #     return super(SaleOrder, self).action_cancel()
    #
    #
    # def _get_destination_location(self):
    #     self.ensure_one()
    #     return self.return_picking_type_id.default_location_dest_id.id


SaleOrder()


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # return_move_ids = fields.One2many('stock.move', 'sale_return_line_id', string='Reservation', readonly=True,
    #                                   ondelete='set null', copy=False)
    qty_received = fields.Float(string="Received Qty", digits=dp.get_precision('Product Unit of Measure'), copy=False)
    # return_move_dest_ids = fields.One2many('stock.move', 'created_return_sale_line_id', 'Downstream Moves')

    qty_to_invoice = fields.Float(
        compute='_get_to_invoice_qty', string='To Invoice Quantity', store=True, readonly=True,
        digits=dp.get_precision('Product Unit of Measure'))

    qty_invoiced = fields.Float(
        compute='_get_invoice_qty', string='Invoiced Quantity', store=True, readonly=True,
        digits=dp.get_precision('Product Unit of Measure'))

    @api.depends('invoice_lines.move_id.state', 'invoice_lines.quantity')
    def _get_invoice_qty(self):

        for line in self:
            qty_invoiced = 0.0
            for invoice_line in line.invoice_lines:
                if invoice_line.move_id.state != 'cancel':
                    if invoice_line.move_id.move_type == 'out_invoice':
                        qty_invoiced += invoice_line.product_uom_id._compute_quantity(invoice_line.quantity, line.product_uom)
                    elif invoice_line.move_id.move_type == 'out_refund' and line.product_uom_qty < 0:
                        qty_invoiced = invoice_line.product_uom_id._compute_quantity(invoice_line.quantity, line.product_uom)
                    elif invoice_line.move_id.move_type == 'out_refund' and line.product_uom_qty > 0:
                        qty_invoiced -= invoice_line.product_uom_id._compute_quantity(invoice_line.quantity, line.product_uom)
            line.qty_invoiced = qty_invoiced

    @api.depends('qty_invoiced', 'qty_delivered', 'qty_received', 'product_uom_qty', 'order_id.state')
    def _get_to_invoice_qty(self):

        for line in self:
            if line.order_id.state in ['sale', 'done']:
                if line.product_id.invoice_policy == 'order':
                    if line.product_uom_qty < 0:
                        line.qty_to_invoice = line.product_uom_qty * -1 - line.qty_invoiced
                    else:
                        line.qty_to_invoice = line.product_uom_qty - line.qty_invoiced
                else:
                    if line.product_uom_qty < 0:
                        line.qty_to_invoice = line.qty_received - line.qty_invoiced
                    else:
                        line.qty_to_invoice = line.qty_delivered - line.qty_invoiced
            else:
                line.qty_to_invoice = 0

    @api.model
    def create(self, values):
        line = super(SaleOrderLine, self).create(values)
        if line.order_id.state == 'purchase':
            line._create_or_update_picking()
        return line

    
    # def write(self, values):
    #     result = super(SaleOrderLine, self).write(values)
    #     # Update expected date of corresponding moves
    #     if 'date_planned' in values:
    #         self.env['stock.move'].search([
    #             ('sale_return_line_id', 'in', self.ids), ('state', '!=', 'done')
    #         ]).write({'date_expected': values['date_planned']})
    #     if 'product_uom_qty' in values:
    #         self.filtered(lambda l: l.order_id.state == 'sale')._create_or_update_picking()
    #     return result

    
    # def _create_or_update_picking(self):
    #     for line in self:
    #         if line.product_id.type in ('product', 'consu'):
    #             # Prevent decreasing below received quantity
    #             if float_compare(line.product_uom_qty * -1, line.qty_received, line.product_uom.rounding) < 0:
    #                 raise UserError(_('You cannot decrease the ordered quantity below the received quantity.\n'
    #                                   'Create a return first.'))
    #
    #             if float_compare(line.product_uom_qty * -1, line.qty_invoiced, line.product_uom.rounding) == -1:
    #                 activity = self.env['mail.activity'].sudo().create({
    #                     'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
    #                     'note': _(
    #                         'The quantities on your purchase order indicate less than billed. You should ask for a refund. '),
    #                     'res_id': line.invoice_lines[0].invoice_id.id,
    #                     'res_model_id': self.env.ref('account.model_account_invoice').id,
    #                 })
    #                 activity._onchange_activity_type_id()
    #
    #             # If the user increased quantity of existing line or created a new line
    #             pickings = line.order_id.return_picking_ids.filtered(
    #                 lambda x: x.state not in ('done', 'cancel') and x.location_dest_id.usage in ('internal', 'transit'))
    #             picking = pickings and pickings[0] or False
    #             if not picking:
    #                 res = line.order_id._prepare_picking()
    #                 picking = self.env['stock.picking'].create(res)
    #             move_vals = line._prepare_stock_moves(picking)
    #             for move_val in move_vals:
    #                 self.env['stock.move'] \
    #                     .create(move_val) \
    #                     ._action_confirm() \
    #                     ._action_assign()
    #
    #
    # def _get_stock_move_price_unit(self):
    #     self.ensure_one()
    #     line = self[0]
    #     order = line.order_id
    #     price_unit = line.price_unit
    #     if line.tax_id:
    #         price_unit = line.tax_id.with_context(round=False).compute_all(
    #             price_unit, currency=line.order_id.currency_id, quantity=1.0, product=line.product_id,
    #             partner=line.order_id.partner_id
    #         )['total_excluded']
    #     if line.product_uom.id != line.product_id.uom_id.id:
    #         price_unit *= line.product_uom.factor / line.product_id.uom_id.factor
    #     if order.currency_id != order.company_id.currency_id:
    #         price_unit = order.currency_id._convert(
    #             price_unit, order.company_id.currency_id, self.company_id, self.date_order or fields.Date.today(),
    #             round=False)
    #     return price_unit
    #
    #
    # def _prepare_stock_moves(self, picking):
    #     """ Prepare the stock moves data for one order line. This function returns a list of
    #     dictionary ready to be used in stock.move's create()
    #     """
    #     self.ensure_one()
    #     res = []
    #     if self.product_id.type not in ['product', 'consu']:
    #         return res
    #     qty = 0.0
    #     price_unit = self._get_stock_move_price_unit()
    #     for move in self.return_move_ids.filtered(
    #             lambda x: x.state != 'cancel' and not x.location_dest_id.usage == "supplier"):
    #         qty += move.product_uom._compute_quantity(move.product_uom_qty, self.product_uom, rounding_method='HALF-UP')
    #     template = {
    #         'name': self.name or '',
    #         'product_id': self.product_id.id,
    #         'product_uom': self.product_uom.id,
    #         'date': self.order_id.date_order,
    #         'date_expected': self.order_id.date_order,
    #         'location_id': self.order_id.partner_id.property_stock_customer.id,
    #         'location_dest_id': self.order_id._get_destination_location(),
    #         'picking_id': picking.id,
    #         'partner_id': self.order_id.partner_id.id,
    #         'return_move_dest_ids': [(4, x) for x in self.return_move_dest_ids.ids],
    #         'state': 'draft',
    #         'sale_return_line_id': self.id,
    #         'company_id': self.order_id.company_id.id,
    #         'price_unit': price_unit,
    #         'picking_type_id': self.order_id.return_picking_type_id.id,
    #         'group_id': self.order_id.return_group_id.id,
    #         'origin': self.order_id.name,
    #         'route_ids': self.order_id.return_picking_type_id.warehouse_id and [
    #             (6, 0, [x.id for x in self.order_id.return_picking_type_id.warehouse_id.route_ids])] or [],
    #         'warehouse_id': self.order_id.return_picking_type_id.warehouse_id.id,
    #     }
    #     diff_quantity = self.product_uom_qty * -1 - qty
    #     if float_compare(diff_quantity, 0.0, precision_rounding=self.product_uom.rounding) > 0:
    #         quant_uom = self.product_id.uom_id
    #         get_param = self.env['ir.config_parameter'].sudo().get_param
    #         if self.product_uom.id != quant_uom.id and get_param('stock.propagate_uom') != '1':
    #             product_uom_qty = self.product_uom._compute_quantity(diff_quantity, quant_uom,
    #                                                                  rounding_method='HALF-UP')
    #             template['product_uom'] = quant_uom.id
    #             template['product_uom_qty'] = product_uom_qty
    #         else:
    #             template['product_uom_qty'] = diff_quantity
    #         res.append(template)
    #     return res
    #
    #
    # def _create_stock_moves(self, picking):
    #     moves = self.env['stock.move']
    #     done = self.env['stock.move'].browse()
    #     for line in self:
    #         for val in line._prepare_stock_moves(picking):
    #             done += moves.create(val)
    #     return done
    #
    # def _update_received_qty(self):
    #     for line in self:
    #         total = 0.0
    #         for move in line.return_move_ids:
    #             if move.state == 'done':
    #                 if move.location_dest_id.usage == "supplier":
    #                     if move.to_refund:
    #                         total -= move.product_uom._compute_quantity(move.product_uom_qty, line.product_uom)
    #                 else:
    #                     total += move.product_uom._compute_quantity(move.product_uom_qty, line.product_uom)
    #         line.qty_received = total


SaleOrderLine()

from odoo import models, api
from odoo.exceptions import UserError
from odoo.tools.translate import _

class AccountMove(models.AbstractModel):
    _inherit = "account.move"

    def print_receipt(self):
        return self.env.ref('eq_pos_receipt_backend.invoice_receipt_pdf').report_action(self)

    def _amount_to_words(self, amount):
        return (self.currency_id.with_context(lang='en_US').amount_to_text(amount).replace(",", " And ")).replace("،", " And ")
    def _arabic_amount_to_words(self, amount):
        return  (self.currency_id.with_context(lang='ar_001').amount_to_text(amount).replace(",", "و")).replace("،", " و")

    def get_order_tax_value_in_receipt(self):
        fiscal_position_id = self.fiscal_position_id
        taxes_dict = {}
        for line in self.invoice_line_ids:
            taxes = line.tax_ids.filtered(lambda t: t.company_id.id == self.company_id.id)
            if fiscal_position_id:
                taxes = fiscal_position_id.map_tax(taxes, line.product_id, self.partner_id)
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = taxes.compute_all(price, self.currency_id, line.quantity, product=line.product_id,
                                      partner=self.partner_id or False)['taxes']
            for each_line_tax in taxes:
                taxes_dict.setdefault(each_line_tax['name'], 0.0)
                taxes_dict[each_line_tax['name']] += each_line_tax['amount']
        return taxes_dict

    def get_total_discount_in_receipt(self):
        total_discount = 0.0
        for line in self.invoice_line_ids:
            if line.discount:
                total_discount += (line.quantity * line.price_unit - line.price_subtotal)
        return total_discount






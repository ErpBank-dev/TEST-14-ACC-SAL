from odoo import models, api
from odoo.exceptions import UserError
from odoo.tools.translate import _

class InvoiceReceiptPDF(models.AbstractModel):
    _name = "report.eq_pos_receipt_backend.invoice_receipt_pdf_template"

    @api.model
    def _get_report_values(self, docids, data):
        docs=self.env['account.move'].browse(docids)
        order_ids=[]
        for item in docs:
            if item.pos_order_ids:
                    order_ids.extend(item.pos_order_ids.ids)
        if not order_ids:
            raise UserError(_("No Receipt Found For this Invoice"))
        docs=self.env['pos.order'].browse(order_ids)
        docargs = {
            'doc_ids': [],
            'doc_model': ['pos.order'],
            'docs': docs,
        }
        return docargs
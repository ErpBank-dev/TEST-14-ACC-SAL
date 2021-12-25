from odoo.exceptions import UserError
from odoo import models, fields, api, _
from odoo.http import request
import qrcode, base64
from io import BytesIO
from odoo import http
from datetime import datetime ,timedelta ,time


class QRCodeAddon(models.Model):
    _inherit = 'account.move'
    date_issue = fields.Date(string="Date of Issue")
    date_supply = fields.Date(string="Date of Supply")
    invoice_datetime = fields.Datetime(string="invoice Datetime",compute='_get_invoice_datetime',store=True)
    po_ref=fields.Char()
    po_date=fields.Date()

    @api.depends('invoice_date')
    def _get_invoice_datetime(self):
        for rec in self:
            if rec.invoice_date != False:
                hour=int(datetime.now().strftime('%H'))
                second=int(datetime.now().strftime('%M'))
                minute=int(datetime.now().strftime('%S'))
                year=int(rec.invoice_date.strftime('%Y'))
                month=int(rec.invoice_date.strftime('%m'))
                day=int(rec.invoice_date.strftime('%d'))
                rec.invoice_datetime=datetime(year,month,day,hour,second,minute)
            else:
                rec.invoice_datetime=False


    def net_amount_to_words(self, amount):
        return (self.currency_id.with_context(lang='en_US').amount_to_text(amount).replace(",", " And ")).replace("،", " And ")
    def net_arabic_amount_to_words(self, amount):
        return  (self.currency_id.with_context(lang='ar_001').amount_to_text(amount).replace(",", " و ")).replace("،", " و ")

    def create_qr_code(self, url):
        qr = qrcode.QRCode(version=1,error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=20, border=4, )
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image()
        temp = BytesIO()
        img.save(temp, format="PNG")
        qr_img = base64.b64encode(temp.getvalue())
        return qr_img

    qr_code_image = fields.Binary("QR Code",copy=False,readonly=1,store=True)

    def generate_qr_code(self):
        for rec in self:
            url = rec.sudo().get_portal_url(report_type='pdf')
            system_parameter_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
            rec.qr_code_image = rec.sudo().create_qr_code(system_parameter_url+url)
            return rec.qr_code_image


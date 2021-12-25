from odoo import models, fields,tools, _
import logging

_logger = logging.getLogger(__name__)

try:
    from num2words import num2words
except ImportError:
    _logger.warning("The num2words python library is not installed, amount-to-text features won't be fully available.")
    num2words = None

class Company(models.Model):
    _inherit = 'res.company'
    company_report_header = fields.Binary()
    company_report_footer = fields.Binary()
    company_name_ar = fields.Char(string=_("Company Name Arabic"))
    main_commercial_register = fields.Char(string=_("Commercial Register"))
    sub_commercial_register = fields.Char(string=_("Sub Commercial Register"))
    precious_metals_register_no = fields.Char(string=_("Precious Metals Register No."))

class Currency(models.Model):
    _inherit = "res.currency"
    currency_unit_label = fields.Char(string="Currency Unit", help="Currency Unit Name",translate=True)
    currency_subunit_label = fields.Char(string="Currency Subunit", help="Currency Subunit Name",translate=True)


    def amount_to_text(self, amount):
        self.ensure_one()

        def _num2words(number, lang):
            try:
                return num2words(number, lang=lang).title()
            except NotImplementedError:
                return num2words(number, lang='en').title()

        if num2words is None:
            logging.getLogger(__name__).warning("The library 'num2words' is missing, cannot render textual amounts.")
            return ""
        formatted = "%.{0}f".format(self.decimal_places) % amount
        parts = formatted.partition('.')
        integer_value = int(parts[0])
        fractional_value = int(parts[2] or 0)
        lang_code = self.env.context.get('lang') or self.env.user.lang
        lang = self.env['res.lang'].with_context(active_test=False).search([('code', '=', lang_code)])
        if lang_code == 'ar_001':
            amount_words = tools.ustr('{amt_value} {amt_word}').format(
                amt_value=_num2words(integer_value, lang=lang.iso_code),
                amt_word='ريال',
            )
            if not self.is_zero(amount - integer_value):
                amount_words += ' ' + _('و') + tools.ustr(' {amt_value} {amt_word}').format(
                    amt_value=_num2words(fractional_value, lang=lang.iso_code),
                    amt_word='هللة',
                )
        else:
            amount_words = tools.ustr('{amt_value} {amt_word}').format(
                amt_value=_num2words(integer_value, lang=lang.iso_code),
                amt_word=self.currency_unit_label,
            )
            if not self.is_zero(amount - integer_value):
                amount_words += ' ' + _('And') + tools.ustr(' {amt_value} {amt_word}').format(
                    amt_value=_num2words(fractional_value, lang=lang.iso_code),
                    amt_word=self.currency_subunit_label,
                )
        return amount_words

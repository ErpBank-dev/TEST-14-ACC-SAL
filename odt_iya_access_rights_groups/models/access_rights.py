# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import Warning, UserError


class Template(models.Model):
    _inherit = 'product.template'

    @api.model
    def create(self, vals):
        if not self.env.user.has_group('odt_iya_access_rights_groups.product_group'):
            raise UserError(_("You can't create Product Template."))
        res = super(Template, self).create(vals)
        return res


class Product(models.Model):
    _inherit = 'product.product'

    @api.model
    def create(self, vals):
        if not self.env.user.has_group('odt_iya_access_rights_groups.product_group'):
            raise UserError(_("You can't create Product."))
        res = super(Product, self).create(vals)
        return res


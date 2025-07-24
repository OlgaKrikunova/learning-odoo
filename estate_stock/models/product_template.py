from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_stock_low = fields.Boolean(compute="_compute_is_stock_low")

    product_category = fields.Selection([("standard", "Standard"), ("premium", "Premium"), ("eco", "Eco")])

    @api.depends()
    def _compute_is_stock_low(self):
        for record in self:
            if record.qty_available < 10:
                record.is_stock_low = True
            else:
                record.is_stock_low = False

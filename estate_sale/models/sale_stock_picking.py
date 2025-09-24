from odoo import fields, models


class SaleStockPicking(models.Model):
    _inherit = "stock.picking"

    shipping_method = fields.Selection(
        selection=[("self_pickup", "Self pickup"), ("pickup_later", "Pickup later"), ("delivery", "Delivery")],
        required=False,
        readonly=False,
        help="Select how the order will be fulfilled.",
    )

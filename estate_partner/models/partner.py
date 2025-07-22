from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    manager_comment = fields.Text(string="Manager's Comment")

    is_vip = fields.Boolean(string="VIP client")

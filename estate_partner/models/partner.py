from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = "res.partner"

    manager_comment = fields.Text(string="Manager's Comment")

    is_vip = fields.Boolean(string="VIP client")

    @api.ondelete(at_uninstall=False)
    def _check_partner_orders(self):
        for partner in self:
            if partner.sale_order_ids:
                raise UserError(_("It is not possible to delete a client with orders."))

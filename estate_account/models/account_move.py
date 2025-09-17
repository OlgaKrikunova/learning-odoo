from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    total_with_tax = fields.Monetary(compute="_compute_total_with_tax", help="This is an amount including taxes.")
    shipping_method = fields.Selection(
        selection=[("self_pickup", "Self pickup"), ("pickup_later", "Pickup later"), ("delivery", "Delivery")],
        required=False,
        readonly=False,
        help="Select how the order will be fulfilled.",
    )

    @api.depends("amount_total", "amount_tax")
    def _compute_total_with_tax(self):
        for record in self:
            record.total_with_tax = record.amount_untaxed + record.amount_tax

    def delete_draft_invoices(self):
        draft_to_delete = self.filtered(lambda x: x.state == "draft")

        draft_to_delete.unlink()

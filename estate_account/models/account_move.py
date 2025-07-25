from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    total_with_tax = fields.Monetary(compute="_compute_total_with_tax", help="This is an amount including taxes.")

    @api.depends("amount_total", "amount_tax")
    def _compute_total_with_tax(self):
        for record in self:
            record.total_with_tax = record.amount_untaxed + record.amount_tax

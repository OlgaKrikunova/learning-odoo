from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    internal_note = fields.Text()
    team_id = fields.Many2one(default=False)

    def send_internal_email(self):
        template = self.env.ref("estate_sale.mail_template_sale_internal_email")
        # We use force_send to send the email or get exception immediately and return message to the user
        template.send_mail(
            self.id,
            force_send=True,
            email_values={
                "email_to": self.env.user.email,
            },
            email_layout_xmlid="mail.mail_notification_light",
        )
        return True

    is_big_order = fields.Boolean(compute="_compute_big_order", store=True)

    @api.depends("amount_total")
    def _compute_big_order(self):
        for record in self:
            record.is_big_order = record.amount_total > 1000

    line_count = fields.Integer(string="Number of positions", compute="_compute_line_count")

    def _compute_line_count(self):
        for rec in self:
            rec.line_count = len(rec.order_line)

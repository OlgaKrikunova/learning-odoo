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

    def action_duplicate_lines_to_new_order(self):
        for order in self:
            # create a new order
            new_order = self.env["sale.order"].create(
                {
                    "partner_id": order.partner_id.id,
                    "user_id": order.user_id.id,
                    "origin": f"Copied from {order.name}",
                }
            )

            # create order lines (without discounts)
            line_vals = []
            for line in order.order_line:
                line_vals.append(
                    {
                        "order_id": new_order.id,
                        "product_id": line.product_id.id,
                        "product_uom_qty": line.product_uom_qty,
                        "product_uom": line.product_uom.id,
                        "price_unit": line.price_unit,
                        "discount": 0.0,
                        "name": line.name,
                    }
                )
            self.env["sale.order.line"].create(line_vals)

            # return action to open a new order
            return {
                "type": "ir.actions.act_window",
                "name": "New Sale Order",
                "res_model": "sale.order",
                "view_mode": "form",
                "res_id": new_order.id,
                "target": "current",
            }

    line_count = fields.Integer(string="Number of positions", compute="_compute_line_count")

    def _compute_line_count(self):
        for rec in self:
            rec.line_count = len(rec.order_line)

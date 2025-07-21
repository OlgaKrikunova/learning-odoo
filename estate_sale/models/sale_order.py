from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    internal_note = fields.Text()

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

from odoo import Command, models


class EstateProperty(models.Model):
    _inherit = "estate.property"

    def estate_property_action_sold(self):
        result = super().estate_property_action_sold()
        for property in self:
            property_name = property.name
            commission = property.selling_price * 0.06 if property.selling_price else 0.0
            admin_fee = 100.0

            move_vals = {
                "partner_id": property.buyer_id.id,
                "move_type": "out_invoice",
                "invoice_line_ids": [
                    Command.create(
                        {
                            "name": f" {property_name} (commission 6% of sale price)",
                            "quantity": 1,
                            "price_unit": commission,
                        }
                    ),
                    Command.create(
                        {
                            "name": "Administrative fee",
                            "quantity": 1,
                            "price_unit": admin_fee,
                        }
                    ),
                    Command.create(
                        {
                            "name": f" {property_name} (sale price)",
                            "quantity": 1,
                            "price_unit": property.selling_price,
                        }
                    ),
                ],
            }

            self.check_access("write")
            self.env["account.move"].sudo().create(move_vals)

        return result

from odoo import models


class Warehouse(models.Model):
    _inherit = "stock.warehouse"

    def action_create_order_from_warehouse(self):
        return {
            "type": "ir.actions.act_window",
            "name": "New Sale Order",
            "res_model": "sale.order",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_warehouse_id": self.id,
            },
        }

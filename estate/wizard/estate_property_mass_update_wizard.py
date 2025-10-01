from odoo import api, fields, models


class EstatePropertyMassUpdateWizard(models.TransientModel):
    _name = "estate.property.mass.update.wizard"
    _description = "Wizard: Mass Update Estate Property Status"

    state = fields.Selection(
        selection=[
            ("new", "New"),
            ("offer_received", "Offer Received"),
            ("offer_accepted", "Offer Accepted"),
            ("sold", "Sold"),
            ("cancelled", "Cancelled"),
        ],
        copy=False,
        required=True,
        default="new",
        string="Status",
    )

    property_ids = fields.Many2many(
        "estate.property",
        string="Properties",
        readonly=True,
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_ids = self.env.context.get("active_ids", [])
        if active_ids:
            res["property_ids"] = [(6, 0, active_ids)]
        return res

    def action_apply(self):
        active_ids = self.env.context.get("active_ids", [])
        if active_ids:
            self.env["estate.property"].browse(active_ids).write({"state": self.state})
        return {"type": "ir.actions.act_window_close"}

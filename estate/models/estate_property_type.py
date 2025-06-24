from odoo import api, fields, models


class EstatePropertyType(models.Model):
    _name = "estate.property.type"
    _description = "Property Types"
    _order = "sequence, name"

    name = fields.Char(required=True)
    sequence = fields.Integer(default=1, help="Used to order stages. Lower is better.")

    property_ids = fields.One2many("estate.property", "property_type_id", string="Properties")

    offer_ids = fields.One2many(comodel_name="estate.property.offer", inverse_name="property_type_id", string="Offers")

    offer_count = fields.Integer(compute="_compute_offer_count")

    @api.depends("offer_ids")
    def _compute_offer_count(self):
        for record in self:
            record.offer_count = len(record.offer_ids)

    _sql_constraints = [
        ("unique_name", "UNIQUE (name)", "The name of the module must be unique!"),
    ]

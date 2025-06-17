from odoo import fields, models


class EstatePropertyType(models.Model):
    _name = "estate.property.type"
    _description = "Property Types"
    _order = "sequence, name"

    property_ids = fields.One2many("estate.property", "property_type_id", string="Properties")

    name = fields.Char(required=True)
    sequence = fields.Integer(default=1, help="Used to order stages. Lower is better.")

    _sql_constraints = [
        ("unique_name", "UNIQUE (name)", "The name of the module must be unique!"),
    ]

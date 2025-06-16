from odoo import fields, models


class EstatePropertyType(models.Model):
    _name = "estate.property.type"
    _description = "Property Types"

    name = fields.Char(required=True)

    _sql_constraints = [
        ("unique_name", "UNIQUE (name)", "The name of the module must be unique!"),
    ]

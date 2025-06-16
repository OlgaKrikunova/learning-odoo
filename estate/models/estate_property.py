from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, float_is_zero


class EstateProperty(models.Model):
    _name = "estate.property"
    _description = "Estate Property"

    name = fields.Char(required=True)
    description = fields.Text()
    postcode = fields.Char()
    date_availability = fields.Date(copy=False, default=fields.Date.today() + timedelta(days=90))
    expected_price = fields.Float(required=True)
    selling_price = fields.Float(readonly=True, copy=False)
    bedrooms = fields.Integer(default=2)
    living_area = fields.Integer()
    facades = fields.Integer()
    garage = fields.Boolean()
    garden = fields.Boolean()
    garden_area = fields.Integer()
    garden_orientation = fields.Selection(
        string="Type", selection=[("north", "North"), ("south", "South"), ("east", "East"), ("west", "West")]
    )
    active = fields.Boolean(default=True)
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
    )
    property_type_id = fields.Many2one(
        "estate.property.type",
        string="Property Type",
    )

    salesman_id = fields.Many2one("res.users", string="Salesman", default=lambda self: self.env.user)

    buyer_id = fields.Many2one("res.partner", string="Buyer", copy=False)

    tag_ids = fields.Many2many(comodel_name="estate.property.tag", string="Tags")

    offer_ids = fields.One2many(comodel_name="estate.property.offer", inverse_name="property_id", string="Offers")

    total_area = fields.Float(compute="_compute_total_area")

    @api.depends("living_area", "garden_area")
    def _compute_total_area(self):
        for record in self:
            record.total_area = record.living_area + record.garden_area

    best_price = fields.Float(compute="_compute_best_price")

    @api.depends("offer_ids")
    def _compute_best_price(self):
        for record in self:
            prices = record.offer_ids.mapped("price")
            record.best_price = max(prices) if prices else 0.0
            # record.best_price = max(record.offer_ids.mapped("price"))

    @api.onchange("garden")
    def _onchange_garden(self):
        if self.garden:
            self.garden_area = 10
            self.garden_orientation = "north"

        else:
            self.garden_area = 0
            self.garden_orientation = ""

    def estate_property_action_sold(self):
        for record in self:
            if record.state == "cancelled":
                raise UserError(_("Cancelled property cannot be marked as sold."))
            record.state = "sold"

    def estate_property_action_cancel(self):
        for record in self:
            if record.state == "sold":
                raise UserError(_("Sold property cannot be cancelled."))
            record.state = "cancelled"

    _sql_constraints = [
        ("check_expected_price", "CHECK(expected_price > 0)", "Expected price must be greater than 0.00."),
        ("check_selling_price", "CHECK(selling_price > 0)", "Selling price must be strictly positive."),
    ]

    @api.constrains("selling_price", "expected_price")
    def _check_selling_price(self):
        precision = 2
        for record in self:
            if float_is_zero(record.selling_price, precision_digits=precision):
                continue

            if float_is_zero(record.expected_price, precision_digits=precision):
                continue

            accepted_offer = record.offer_ids.filtered(lambda o: o.status == "accepted")
            if not accepted_offer:
                continue

            min_price = record.expected_price * 0.9

            if float_compare(record.selling_price, min_price, precision_digits=precision) < 0:
                raise ValidationError(_("The selling price cannot be lower than 90% of the expected price."))

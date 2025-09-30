from datetime import datetime, timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare


class EstateProperty(models.Model):
    _name = "estate.property"
    _description = "Estate Property"
    _order = "id desc"

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
        string="Status",
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

    best_price = fields.Float(compute="_compute_best_price")

    company_id = fields.Many2one("res.company", string="Company", required=True, default=lambda self: self.env.company)

    construction_year = fields.Integer(default=datetime.now().year)

    age = fields.Char(compute="_compute_age")

    discount_applied = fields.Boolean(default=False)

    cancel_discount = fields.Boolean(default=False)

    original_price = fields.Float()

    average_offer_price = fields.Float(compute="_compute_average_offer_price", store=True)

    accept_highest_offer = fields.Boolean(default=False)
    cancel_highest_offer = fields.Boolean(default=False)

    sold_date = fields.Date(copy=False)

    is_favourite = fields.Boolean(string="Mark as Favorite", default=False)

    @api.depends("living_area", "garden_area")
    def _compute_total_area(self):
        for record in self:
            record.total_area = record.living_area + record.garden_area

    @api.depends("offer_ids")
    def _compute_best_price(self):
        for record in self:
            prices = record.offer_ids.mapped("price")
            record.best_price = max(prices) if prices else 0.0

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
            accepted_offer = record.offer_ids.filtered(lambda o: o.status == "accepted")
            if not accepted_offer:
                continue

            min_price = record.expected_price * 0.9

            if float_compare(record.selling_price, min_price, precision_digits=precision) < 0:
                raise ValidationError(_("The selling price cannot be lower than 90% of the expected price."))

    @api.ondelete(at_uninstall=False)
    def _unlink_if_state(self):
        for record in self:
            if record.state not in ("new", "cancelled"):
                raise UserError(_("Only New and Cancelled properties can be deleted."))

    def _compute_age(self):
        current_year = datetime.now().year
        for record in self:
            if record.construction_year:
                record.age = current_year - record.construction_year
            else:
                record.age = 0

    def action_apply_discount(self):
        for record in self:
            if record.discount_applied:
                raise UserError(_("Discount was already applied!"))

            record.original_price = record.expected_price

            new_price = record.expected_price * 0.9
            if new_price < 1000:
                raise ValidationError(_("Price must be at least 1000!"))

            record.expected_price = new_price
            record.discount_applied = True

    def cancel_apply_discount(self):
        for record in self:
            if not record.discount_applied:
                raise UserError(_("Discount was not applied!"))

            record.expected_price = record.original_price
            record.discount_applied = False

    @api.depends("offer_ids.price")
    def _compute_average_offer_price(self):
        for record in self:
            offers = record.offer_ids
            if offers:
                total_sum = sum(offers.mapped("price"))
                count = len(offers)
                record.average_offer_price = total_sum / count

            else:
                record.average_offer_price = 0

    def action_accept_highest_offer(self):
        for record in self:
            record.accept_highest_offer = True
            if record.state == "sold":
                raise UserError(_("Property is already sold!"))

            offers = record.offer_ids
            if not offers:
                raise UserError(_("There are no offers to accept!"))

            best_offer = max(offers, key=lambda offer: offer.price)
            record.buyer_id = best_offer.partner_id
            best_offer.status = "accepted"
            (offers - best_offer).write({"status": "refused"})

            record.state = "sold"
            record.sold_date = fields.Date.today()

    def cancel_accept_highest_offer(self):
        for record in self:
            record.accept_highest_offer = False
            if record.state != "sold":
                raise UserError(_("Property is not sold!"))

            record.state = "new"
            record.sold_date = False
            record.buyer_id = False

    def action_is_favourite(self):
        for record in self:
            record.is_favourite = not record.is_favourite

        return True

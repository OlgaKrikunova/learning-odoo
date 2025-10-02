from datetime import datetime, timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class EstatePropertyOffer(models.Model):
    _name = "estate.property.offer"
    _description = "Property Offer"
    _order = "price desc"

    price = fields.Float()
    status = fields.Selection(
        copy=False, selection=[("accepted", "Accepted"), ("refused", "Refused"), ("expired", "Expired")]
    )
    partner_id = fields.Many2one("res.partner", required=True)
    property_id = fields.Many2one("estate.property", required=True, ondelete="cascade")
    property_type_id = fields.Many2one(
        related="property_id.property_type_id", comodel_name="estate.property.type", store=True, readonly=False
    )

    validity = fields.Integer(default=7)
    date_deadline = fields.Date(compute="_compute_date_deadline", inverse="_inverse_date_deadline", store=True)

    date_create = fields.Date(default=fields.Date.today())

    @api.depends("validity")
    def _compute_date_deadline(self):
        for offer in self:
            base_date = offer.create_date.date() if offer.create_date else fields.Date.today()
            if offer.validity:
                offer.date_deadline = base_date + timedelta(days=offer.validity)
            else:
                offer.date_deadline = False

    def _inverse_date_deadline(self):
        for offer in self:
            base_date = offer.create_date.date() if offer.create_date else fields.Date.context_today(offer)
            if offer.date_deadline:
                delta = offer.date_deadline - base_date
                offer.validity = delta.days

    @api.constrains("validity")
    def _check_validity_within_60_days(self):
        for offer in self:
            if offer.validity > 60:
                raise ValidationError(_("Deadline cannot be more than 60 days from the creation date."))

    @api.model
    def default_get(self, fields_names):
        res = super().default_get(fields_names)
        if "validity" in res and res["validity"] is not None:
            res["date_deadline"] = fields.Date.today() + timedelta(days=res["validity"])
        return res

    def action_accept(self):
        for offer in self:
            if offer.status != "accepted":
                other_offers = offer.property_id.offer_ids - offer
                other_offers.status = "refused"
                offer.status = "accepted"
                offer.property_id.write(
                    {
                        "buyer_id": offer.partner_id.id,
                        "selling_price": offer.price,
                        "state": "offer_accepted",
                    }
                )

    def action_refuse(self):
        for offer in self:
            if offer.status != "refused":
                offer.status = "refused"

    _sql_constraints = [("check_price", "CHECK(price > 0)", "Offer price must be strictly positive.")]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            property = self.env["estate.property"].browse(vals["property_id"])

            for offer in property.offer_ids:
                if vals["price"] < offer.price:
                    raise UserError(_("The offer must be higher than %.2f.", offer.price))

        offers = super().create(vals_list)

        for offer in offers:
            if offer.property_id.state == "new":
                offer.property_id.state = "offer_received"

        return offers

    @api.constrains("property_id", "partner_id", "status")
    def _check_unique_offer(self):
        for offer in self:
            check = self.search(
                [
                    ("property_id", "=", offer.property_id.id),
                    ("partner_id", "=", offer.partner_id.id),
                    ("status", "!=", "refused"),
                    ("id", "!=", offer.id),
                ]
            )

            if check:
                raise ValidationError(_("This buyer has already made an offer on this property."))

    @api.model
    def check_expired_offers(self):
        check = datetime.now() - timedelta(days=30)
        old_offers = self.search(
            [("status", "not in", ["accepted", "refused", "expired"]), ("create_date", "<", check)]
        )
        old_offers.write({"status": "expired"})
        return True

from datetime import timedelta

from odoo import api, fields, models


class EstatePropertyOffer(models.Model):
    _name = "estate.property.offer"
    _description = "Property Offer"

    price = fields.Float()
    status = fields.Selection(copy=False, selection=[("accepted", "Accepted"), ("refused", "Refused")])
    partner_id = fields.Many2one("res.partner", required=True)
    property_id = fields.Many2one("estate.property", required=True)

    validity = fields.Integer(default=7)
    date_deadline = fields.Date(compute="_compute_date_deadline", inverse="_inverse_date_deadline", store=True)

    @api.depends("validity")
    def _compute_date_deadline(self):
        for offer in self:
            base_date = offer.create_date.date() if offer.create_date else fields.Date.context_today(offer)
            if offer.validity is not None:
                offer.date_deadline = base_date + timedelta(days=offer.validity)
            else:
                offer.date_deadline = False

    def _inverse_date_deadline(self):
        for offer in self:
            base_date = offer.create_date.date() if offer.create_date else fields.Date.context_today(offer)
            if offer.date_deadline:
                delta = offer.date_deadline - base_date
                offer.validity = delta.days

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
                other_offers.write({"status": "refused"})
                offer.status = "accepted"
                offer.property_id.write(
                    {
                        "buyer_id": offer.partner_id.id,
                        "selling_price": offer.price,
                    }
                )

    def action_refuse(self):
        for offer in self:
            if offer.status != "refused":
                offer.status = "refused"

    _sql_constraints = [("check_price", "CHECK(price > 0)", "Offer price must be strictly positive.")]

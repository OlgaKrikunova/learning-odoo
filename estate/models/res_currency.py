import logging
from datetime import timedelta

from odoo import fields, models

_logger = logging.getLogger(__name__)


class ResCurrency(models.Model):
    _name = "res.currency"
    _inherit = ["res.currency", "mail.thread", "mail.activity.mixin"]

    def check_currency_cron(self):
        companies = self.env["res.company"].search([("active", "=", True)])
        verification_time = fields.Date.today() - timedelta(days=1)
        currencies = self.search([("active", "=", True)])

        # result = self.env["res.currency.rate"].read_group(
        #     domain=[("company_id", "=", companies.id), ("name", "=", verification_time),
        #             ("currency_id", "=", currencies.id)],
        #     groupby=["currency_id"],
        #     fields=["id:count"],
        # )

        self.env.cr.execute(
            """
            SELECT  currency_id,
            COUNT(company_id)
            FROM res_currency_rate
            WHERE company_id IN %s AND currency_id IN %s AND name = %s
            GROUP BY currency_id
            """,
            (tuple(companies.ids), tuple(currencies.ids), verification_time),
        )
        res_currency = self.env.cr.dictfetchall()

        res = {r["currency_id"]: r["count"] for r in res_currency}

        for currency in currencies:
            if res.get(currency.id, 0) < len(companies):
                currency.activity_schedule(
                    act_type_xmlid="mail.mail_activity_data_todo",
                    summary="No rate update for %s" % currency.name,
                    date_deadline=fields.Date.today(),
                )

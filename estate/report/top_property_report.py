from odoo import api, models


class ReportPropertyTop(models.AbstractModel):
    _name = "report.estate.report_property_top"
    _description = "Top 10 Properties by Price"

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env["estate.property"].search([], order="expected_price desc", limit=10)
        return {
            "doc_ids": docs.ids,
            "doc_model": "estate.property",
            "docs": docs,
        }

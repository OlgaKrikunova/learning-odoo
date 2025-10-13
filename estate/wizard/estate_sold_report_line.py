from odoo import fields, models


class EstateSoldReportLine(models.TransientModel):
    _name = "estate.sold.report.line"
    _description = "Estate Sold Report Line"

    report_id = fields.Many2one("estate.sold.report")
    property_id = fields.Many2one("estate.property", string="Property")
    buyer_id = fields.Many2one("res.partner", string="Buyer")
    selling_price = fields.Float()
    salesperson_id = fields.Many2one("res.users", string="Agent")
    sold_date = fields.Datetime()

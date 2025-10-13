import base64
import io
import logging

from openpyxl import Workbook
from openpyxl.styles import Font

from odoo import _, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class EstateSoldReport(models.TransientModel):
    _name = "estate.sold.report"
    _description = "Estate Sold Report"

    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True)
    sold_property_ids = fields.One2many("estate.sold.report.line", "report_id", string="Sold Properties")

    file_data = fields.Binary(readonly=True)
    file_name = fields.Char()
    html_preview = fields.Html(sanitize=False)

    def action_generate_report(self):
        self.ensure_one()
        sold_properties = self.env["estate.property"].search(
            [
                ("state", "=", "sold"),
                ("write_date", ">=", self.date_from),
                ("write_date", "<=", self.date_to),
            ]
        )
        lines = []
        for record in sold_properties:
            lines.append(
                (
                    0,
                    0,
                    {
                        "property_id": record.id,
                        "buyer_id": record.buyer_id.id,
                        "selling_price": record.selling_price,
                        "salesperson_id": record.salesman_id.id,
                        "sold_date": record.write_date,
                    },
                )
            )
        self.write({"sold_property_ids": lines})

        # """create HTML table for preview"""
        html = ""
        if sold_properties:
            html = """
            <table class="table-sm table-bordered" style="margin-top:10px; border-collapse: collapse;">
                <thead style="background-color: #f4f4f4; font-weight: bold;">
                    <tr>
                        <th>Property</th>
                        <th>Buyer</th>
                        <th>Price</th>
                        <th>Agent</th>
                        <th>Sold Date</th>
                    </tr>
                </thead>
                <tbody>
            """

            for rec in sold_properties:
                sold_str = ""
                if rec.write_date:
                    dt_value = rec.write_date
                    if isinstance(dt_value, str):
                        dt_value = fields.Datetime.from_string(dt_value)
                    local_dt = fields.Datetime.context_timestamp(self, dt_value)
                    sold_str = local_dt.strftime("%Y-%m-%d %H:%M")
                html += f"""
                <tr>
                    <td>{rec.name or ""}</td>
                    <td>{rec.buyer_id.name or ""}</td>
                    <td>{rec.selling_price or ""}</td>
                    <td>{rec.salesman_id.name or ""}</td>
                    <td>{sold_str or ""}</td>
                </tr>
                """
            html += "</tbody></table>"
        else:
            html += "<p style='color:red;'>No sold properties found for the selected period.</p>"

        self.html_preview = html

        return {
            "type": "ir.actions.act_window",
            "res_model": "estate.sold.report",
            "view_mode": "form",
            "res_id": self.id,
            "target": "new",
        }

    def action_export_excel_file(self):
        self.ensure_one()

        if not self.sold_property_ids:
            raise UserError(_("No data to export. Please generate the report first."))

        try:
            # """create a book and sheet for excel"""
            wb = Workbook()
            ws = wb.active
            ws.title = "Sold Properties"

            # """create headers"""
            headers = ["Property", "Buyer", "Price", "Agent", "Sold Date"]
            ws.append(headers)

            # """make the title bold"""
            bold = Font(bold=True)
            for cell in ws[1]:
                cell.font = bold

            # """write data by lines wizard"""
            for line in self.sold_property_ids:
                # """local time user"""
                sold_str = ""
                if line.sold_date:
                    try:
                        dt_value = line.sold_date
                        if isinstance(dt_value, str):
                            dt_value = fields.Datetime.from_string(dt_value)

                        local_dt = fields.Datetime.context_timestamp(self, dt_value)

                        sold_str = local_dt.strftime("%Y-%m-%d %H:%M")
                    except (TypeError, ValueError, AttributeError):
                        sold_str = str(line.sold_date)

                row = [
                    line.property_id.name or "",
                    line.buyer_id.name or "",
                    float(line.selling_price or 0.0),
                    line.salesperson_id.name or "",
                    sold_str,
                ]
                ws.append(row)

            # """save"""
            stream = io.BytesIO()
            wb.save(stream)
            stream.seek(0)
            data = stream.getvalue()

            # """Encode in base64 and write to the wizard fields"""
            file_base64 = base64.b64encode(data)
            file_name = f"sold_properties_{self.date_from}_{self.date_to}.xlsx"
            self.write(
                {
                    "file_data": file_base64,
                    "file_name": file_name,
                }
            )
            return {
                "type": "ir.actions.act_url",
                "url": f"/web/content/?model="
                f"{self._name}&id={self.id}&field=file_data&filename_field=file_name&download=false",
                "target": "new",
            }

        except Exception as e:
            _logger.exception("Export to XLSX failed: %s", e)
            raise UserError(_("Failed to generate Excel file: {}").format(e)) from e

        # except Exception as e:
        #     _logger.exception("Export to XLSX failed")
        #     raise UserError(_("Failed to generate Excel file: %s", e))

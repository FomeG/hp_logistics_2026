from odoo import models, api


class ResLangInherit(models.Model):
    _inherit = "res.lang"

    @api.model
    def _set_date_format_ddmmyyyy(self):
        """Set date format to DD/MM/YYYY for all active languages"""
        active_langs = self.search([("active", "=", True)])
        active_langs.write(
            {
                "date_format": "%d/%m/%Y",
                "time_format": "%H:%M:%S",
            }
        )
        return True

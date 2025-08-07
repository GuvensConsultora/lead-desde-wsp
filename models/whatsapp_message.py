from odoo import models, api
from odoo.exceptions import UserError



class WhatsAppMessage(models.Model):
    _inherit = 'whatsapp.message'

    @api.model
    def create(self, vals):
        message = super().create(vals)

        return message

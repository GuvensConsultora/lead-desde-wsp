from odoo import models, api
from odoo.exceptions import UserError



class WhatsAppMessage(models.Model):
    _inherit = 'whatsapp.message'

    @api.model
    def create(self, vals):
        
        # Agregamos texto antes de crear el mensaje
        if 'body' in vals and vals.get('direction') == 'inbound':
            texto_estandar = "[Mensaje recibido por WhatsApp]"
            vals['body'] = f"{texto_estandar}\n{vals['body']}"

        message = super().create(vals)
        
        return message

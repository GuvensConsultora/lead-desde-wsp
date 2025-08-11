from odoo import models, api
import logging
_logger = logging.getLogger(__name__)

class WhatsAppMessage(models.Model):
    _inherit = 'whatsapp.message'

    @api.model_create_multi
    def create(self, vals_list):
        _logger.info("vals_list entrante: %s", vals_list)

        messages = super().create(vals_list)

        _logger.info("IDE MENSAJES: %s", messages)
        #_logger.info("✔️ Mensaje entrante de %s: %s", message.phone, message.body)
                # seguir con la lógica de creación de lead o partner
                
        return messages

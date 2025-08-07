from odoo import models, api
import logging
_logger = logging.getLogger(__name__)

class WhatsAppMessage(models.Model):
    _inherit = 'whatsapp.message'

    @api.model_create_multi
    def create(self, vals_list):
        _logger.info("📨 vals_list entrante en WhatsAppMessage.create: %s", vals_list)

        messages = super().create(vals_list)

        for message in messages:
            if message.direction == 'inbound' and message.phone:
            # lógica extra si querés
                pass

        return messages

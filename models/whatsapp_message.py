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
        rs_msj = self.env['whatsapp.message'].browse(messages.id)
        _logger.info("CONTENIDO: %s", rs_msj.body)
        #_logger.info("✔️ Mensaje entrante de %s: %s", message.phone, message.body)
                # seguir con la lógica de creación de lead o partner
        reply_text = "Gracias por tu mensaje, en breve te responderemos."
        self.env['whatsapp.message'].create({
            'mobile_number': vals_list[0].get('mobile_number'),
            'body': reply_text,
            'direction': 'out'
        })
                
        return messages

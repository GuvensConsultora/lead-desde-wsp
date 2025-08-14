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


        # ==== CREAR LEADS ====
        lead = self.env['crm.lead'].sudo().create({
            'name': rs_msj.subject or "Lead desde WHATSAPP",
            'phone': rs_msj.mobile_number,
            'description': rs_msj.body or '',
        })


        #_logger.info("✔️ Mensaje entrante de %s: %s", message.phone, message.body)
                # seguir con la lógica de creación de lead o partner
        #reply_text = "Gracias por tu mensaje, en breve te responderemos."
        #self.env['whatsapp.message'].create({
        #    'mobile_number': vals_list[0].get('mobile_number'),
        #    'body': reply_text,
        #    'message_type': 'outbound'
        #})
                
        return messages

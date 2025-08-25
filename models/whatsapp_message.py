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

        # ==== Buscar Contacto ====
        contacto = self.env['res.partner'].search([('phone_sanitized','=',rs_msj.mobile_number)], limit=1)
        if contacto:
            _logger.info("NOMBRE DESDE BD: %s. TELÉFONO DESDE BD: %s", contacto.name, contacto.phone_sanitized)
            if contacto.name in contacto.phone_sanitized[-4:]:
                _logger.info("Este contacto %s ya no fue trabajado. ", contacto.name)
                user = self.env['res.user'].search(['id'],'!=', 8)
                _logger.info("Usuario %s", user)
                # ==== CREAR LEADS ====
                #lead = self.env['crm.lead'].sudo().create({
                #    'name': rs_msj.body or "Lead desde WHATSAPP",
                #    'phone': rs_msj.mobile_number,
                #    'description': rs_msj.body or '',
                #})
            else:
                _logger.info("Este contacto %s ya fue trabajado. ", contacto.name)
                _logger.info("Usuario %s", user)
        else:
            _logger.info("No se encontró contacto con ese número: %s", rs_msj.mobile_number.replace('+', ''))

        

        return messages

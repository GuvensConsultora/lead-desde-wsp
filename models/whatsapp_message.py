from odoo import models, api
import logging, random
_logger = logging.getLogger(__name__)

class WhatsAppMessage(models.Model):
    _inherit = 'whatsapp.message'

    @api.model_create_multi
    def create(self, vals_list):
        _logger.info("vals_list entrante: %s", vals_list)

        messages = super().create(vals_list)
        _logger.info("IDE MENSAJES: %s con fecha %s", messages,)
        rs_msj = self.env['whatsapp.message'].browse(messages.id)
        _logger.info("CONTENIDO: %s credo el %s", rs_msj.body, rs_msj.create_date)

        # ==== Buscar Contacto ====
        contacto = self.env['res.partner'].search([('phone_sanitized','=',rs_msj.mobile_number)], limit=1)
        if contacto:
            _logger.info("NOMBRE DESDE BD: %s. TELÉFONO DESDE BD: %s  FECHA DE CREACIÓN: %S", contacto.name, contacto.phone_sanitized, contacto.create_date)
            user = self.env['res.users'].search([('active', '=', True),('id','!=', 8)])
                # ==== CREAR LEADS ====
                #lead = self.env['crm.lead'].sudo().create({
                #    'name': rs_msj.body or "Lead desde WHATSAPP",
                #    'phone': rs_msj.mobile_number,
                #    'description': rs_msj.body or '',
                #})
            _logger.info("Este contacto %s ya fue trabajado. Creado el: %s ", contacto.name, contacto.create_date)
            _logger.info("Usuario %s", user.ids)
        else:
            _logger.info("No se encontró contacto con ese número: %s", rs_msj.mobile_number.replace('+', ''))

        

        return messages

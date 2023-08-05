# -*- coding: utf-8 -*-
# Copyright 2020-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
from odoo import fields, models, api


class RentInvoice(models.Model):
    _name = 'rent.invoice'
    _description = 'Crete Invoice for Rented property'
    _rec_name = 'tenancy_id'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    tenancy_id = fields.Many2one('tenancy.details', string='Tenancy No.')
    customer_id = fields.Many2one(related='tenancy_id.tenancy_id', string='Customer', store=True)
    type = fields.Selection([('deposit', 'Deposit'),
                             ('rent', 'Rent'),
                             ('maintenance', 'Maintenance'),
                             ('penalty', 'Penalty'),
                             ('full_rent', 'Full Rent')],
                            string='Payment', default='rent')
    invoice_date = fields.Date(string='Invoice Date')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Currency')
    rent_amount = fields.Monetary(string='Rent Amount')
    amount = fields.Monetary(string='Rent Amount')
    description = fields.Char(string='Description', translate=True)
    rent_invoice_id = fields.Many2one('account.move', string='Invoice')
    payment_state = fields.Selection(related='rent_invoice_id.payment_state', string="Payment Status")
    landlord_id = fields.Many2one(related="tenancy_id.property_id.landlord_id", store=True)
    is_yearly = fields.Boolean()
    remain = fields.Integer()
    tenancy_type = fields.Selection(related="tenancy_id.type", string="Tenancy Type")
    service_amount = fields.Monetary(string="Service Amount")
    is_extra_service = fields.Boolean(related="tenancy_id.is_extra_service")

    def action_create_invoice(self):
        invoice_lines = []
        amount = 0
        if self.tenancy_id.is_extra_service:
            if self.tenancy_id.payment_term == "monthly":
                for line in self.tenancy_id.extra_services_ids:
                    if line.service_type == "monthly":
                        amount = amount + line.price
                        desc = "Monthly"
                        service_invoice_record = {
                            'product_id': line.service_id.id,
                            'name': desc,
                            'quantity': 1,
                            'price_unit': line.price
                        }
                        invoice_lines.append((0, 0, service_invoice_record))
            if self.tenancy_id.payment_term == "quarterly":
                for line in self.tenancy_id.extra_services_ids:
                    if line.service_type == "monthly":
                        amount = amount + (line.price * (self.remain if self.remain > 0 else 3))
                        desc = "Monthly"
                        service_invoice_record = {
                            'product_id': line.service_id.id,
                            'name': desc,
                            'quantity': self.remain if self.remain > 0 else 3,
                            'price_unit': line.price
                        }
                        invoice_lines.append((0, 0, service_invoice_record))
            if self.tenancy_id.payment_term == "year":
                for line in self.tenancy_id.extra_services_ids:
                    if line.service_type == "monthly":
                        amount = amount + (line.price * 12)
                        desc = "Monthly"
                        service_invoice_record = {
                            'product_id': line.service_id.id,
                            'name': desc,
                            'quantity': 12,
                            'price_unit': line.price
                        }
                        invoice_lines.append((0, 0, service_invoice_record))

        record = {
            'product_id': self.env.ref('rental_management.property_product_1').id,
            'name': self.description,
            'quantity': 1,
            'price_unit': self.amount
        }
        invoice_lines.append((0, 0, record))
        rent_record = {
            'partner_id': self.customer_id.id,
            'move_type': 'out_invoice',
            'invoice_date': self.invoice_date,
            'tenancy_id': self.tenancy_id.id,
            'invoice_line_ids': invoice_lines,
        }
        self.service_amount = amount
        invoice_id = self.env['account.move'].create(rent_record)
        invoice_id.action_post()
        self.rent_invoice_id = invoice_id.id


class TenancyInvoice(models.Model):
    _inherit = 'account.move'

    tenancy_id = fields.Many2one('tenancy.details', readonly=1, string="Tenancy", store=True)
    sold_id = fields.Many2one('property.vendor', string="Sold Information", readonly=1, store=True)
    tenancy_property_id = fields.Many2one(related="tenancy_id.property_id", string="Property")
    sold_property_id = fields.Many2one(related="sold_id.property_id", string="Property ")

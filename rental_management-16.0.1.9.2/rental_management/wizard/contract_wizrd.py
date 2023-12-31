# -*- coding: utf-8 -*-
# Copyright 2020-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
from odoo import fields, models, api


class ContractWizard(models.TransientModel):
    _name = 'contract.wizard'
    _description = 'Create Contract of rent in property'

    # Tenancy
    customer_id = fields.Many2one('res.partner', string='Customer', domain=[('user_type', '=', 'customer')])
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Currency')
    is_any_deposit = fields.Boolean(string="Deposit")
    deposit_amount = fields.Monetary(string="Security Deposit")

    # Property Details
    property_id = fields.Many2one('property.details', string='Property')
    is_extra_service = fields.Boolean(related="property_id.is_extra_service", string="Any Extra Services")
    total_rent = fields.Monetary(related='property_id.tenancy_price', string='Related')
    payment_term = fields.Selection([('monthly', 'Monthly'),
                                     ('full_payment', 'Full Payment'), ('quarterly', 'Quarterly'), ('year', 'Yearly')],
                                    string='Payment Term')
    is_any_broker = fields.Boolean(string='Any Broker?')
    broker_id = fields.Many2one('res.partner', string='Broker', domain=[('user_type', '=', 'broker')])
    duration_id = fields.Many2one('contract.duration', string='Duration')
    start_date = fields.Date(string='Start Date')
    services = fields.Char(string="Added Services", compute="_compute_services", translate=True)

    rent_type = fields.Selection([('once', 'First Month'), ('e_rent', 'All Month')], string='Brokerage Type')
    commission_type = fields.Selection([('f', 'Fix'), ('p', 'Percentage')], string="Commission Type")
    broker_commission = fields.Monetary(string='Commission')
    broker_commission_percentage = fields.Float(string='Percentage')
    from_inquiry = fields.Boolean('From Inquiry')
    inquiry_id = fields.Many2one('tenancy.inquiry', string="Inquiry")
    note = fields.Text(string="Note", translate=True)
    rent_unit = fields.Selection(related="property_id.rent_unit")
    agreement = fields.Html(string="Agreement")
    agreement_template_id = fields.Many2one('agreement.template', string="Agreement Template")

    @api.onchange('payment_term', 'rent_unit', 'duration_id')
    def _onchange_payment_term(self):
        if self.rent_unit == 'Day':
            return {'domain': {'duration_id': [('rent_unit', '=', 'Day')]}}
        if self.rent_unit == "Year":
            return {'domain': {'duration_id': [('rent_unit', '=', 'Year')]}}
        if self.rent_unit == "Month":
            if self.payment_term == 'quarterly':
                return {'domain': {'duration_id': [('month', '>=', 3), ('rent_unit', '=', 'Month')]}}
            elif self.payment_term == 'year':
                return {'domain': {'duration_id': [('rent_unit', '=', 'Year')]}}
            else:
                return {'domain': {'duration_id': [('month', '>', 0), ('rent_unit', '=', 'Month')]}}

    @api.onchange('agreement_template_id')
    def _onchange_agreement_template_id(self):
        for rec in self:
            rec.agreement = rec.agreement_template_id.agreement

    @api.model
    def default_get(self, fields):
        res = super(ContractWizard, self).default_get(fields)
        active_id = self._context.get('active_id')
        property_id = self.env['property.details'].browse(active_id)
        if property_id.rent_unit == 'Day':
            res['payment_term'] = 'full_payment'
        if property_id.rent_unit == 'Year':
            res['payment_term'] = 'year'
        return res

    @api.depends('property_id')
    def _compute_services(self):
        for rec in self:
            s = ""
            if rec.property_id:
                if rec.property_id.is_extra_service:
                    for data in rec.property_id.extra_service_ids:
                        s = s + "{} ,".format(data.service_id.name)
                    rec.services = s
                else:
                    rec.services = ""
            else:
                rec.services = ""

    def contract_action(self):
        service_line = []
        for rec in self:
            if rec.property_id.is_extra_service:
                for data in rec.property_id.extra_service_ids:
                    service_record = {
                        'service_id': data.service_id.id,
                        'service_type': data.service_type,
                        'from_contract': True
                    }
                    service_line.append((0, 0, service_record))

        if self.payment_term == 'monthly':
            self.customer_id.is_tenancy = True
            record = {
                'tenancy_id': self.customer_id.id,
                'property_id': self.property_id.id,
                'is_any_broker': self.is_any_broker,
                'broker_id': self.broker_id.id,
                'duration_id': self.duration_id.id,
                'start_date': self.start_date,
                'total_rent': self.total_rent,
                'contract_type': 'new_contract',
                'payment_term': self.payment_term,
                'rent_type': self.rent_type,
                'commission_type': self.commission_type,
                'broker_commission': self.broker_commission,
                'broker_commission_percentage': self.broker_commission_percentage,
                'is_any_deposit': self.is_any_deposit,
                'deposit_amount': self.deposit_amount,
                'agreement': self.agreement
            }
            if service_line:
                record['extra_services_ids'] = service_line
            contract_id = self.env['tenancy.details'].create(record)

            data = {
                'stage': 'on_lease'
            }
            self.property_id.write(data)
            return {
                'type': 'ir.actions.act_window',
                'name': 'Contract',
                'res_model': 'tenancy.details',
                'res_id': contract_id.id,
                'view_mode': 'form,tree',
                'target': 'current'
            }
        elif self.payment_term == "full_payment":
            record = {
                'tenancy_id': self.customer_id.id,
                'property_id': self.property_id.id,
                'is_any_broker': self.is_any_broker,
                'broker_id': self.broker_id.id,
                'duration_id': self.duration_id.id,
                'start_date': self.start_date,
                'total_rent': self.total_rent,
                'contract_type': 'running_contract',
                'last_invoice_payment_date': fields.Date.today(),
                'payment_term': self.payment_term,
                'rent_type': self.rent_type,
                'commission_type': self.commission_type,
                'broker_commission': self.broker_commission,
                'broker_commission_percentage': self.broker_commission_percentage,
                'active_contract_state': True,
                'is_any_deposit': self.is_any_deposit,
                'deposit_amount': self.deposit_amount,
                'agreement': self.agreement
            }
            if service_line:
                record['extra_services_ids'] = service_line
            contract_id = self.env['tenancy.details'].create(record)
            if contract_id.is_any_broker:
                contract_id.action_broker_invoice()
            data = {
                'stage': 'on_lease'
            }
            self.property_id.write(data)

            # Creating Invoice
            amount = self.property_id.tenancy_price
            total_amount = amount * self.duration_id.month
            service_invoice_line = []
            full_payment_record = {
                'product_id': self.env.ref('rental_management.property_product_1').id,
                'name': 'Full Payment of ' + self.property_id.name,
                'quantity': 1,
                'price_unit': total_amount
            }
            if self.is_any_deposit:
                deposit_record = {
                    'product_id': self.env.ref('rental_management.property_product_1').id,
                    'name': 'Deposit of ' + self.property_id.name,
                    'quantity': 1,
                    'price_unit': self.deposit_amount
                }
                service_invoice_line.append((0, 0, deposit_record))
            service_invoice_line.append((0, 0, full_payment_record))
            for rec in self:
                desc = ""
                if rec.property_id.is_extra_service:
                    for line in rec.property_id.extra_service_ids:
                        if line.service_type == "once":
                            amount = line.price
                            desc = "Once"
                        if line.service_type == "monthly":
                            amount = line.price * self.duration_id.month
                            desc = "Monthly : For " + str(self.duration_id.month) + " Month"
                        service_invoice_record = {
                            'product_id': line.service_id.id,
                            'name': desc,
                            'quantity': 1,
                            'price_unit': amount
                        }
                        service_invoice_line.append((0, 0, service_invoice_record))
            data = {
                'partner_id': self.customer_id.id,
                'move_type': 'out_invoice',
                'invoice_date': fields.date.today(),
                'invoice_line_ids': service_invoice_line
            }
            invoice_id = self.env['account.move'].sudo().create(data)
            invoice_id.tenancy_id = contract_id.id
            invoice_id.action_post()
            amount_total = invoice_id.amount_total
            rent_invoice = {
                'tenancy_id': contract_id.id,
                'type': 'full_rent',
                'invoice_date': fields.date.today(),
                'amount': amount_total,
                'description': 'Full Payment Of Rent',
                'rent_invoice_id': invoice_id.id,
                'rent_amount': amount_total
            }
            if self.is_any_deposit:
                rent_invoice['description'] = 'Full Payment Of Rent + Deposit'
            else:
                rent_invoice['description'] = 'Full Payment Of Rent'
            self.env['rent.invoice'].create(rent_invoice)
            return {
                'type': 'ir.actions.act_window',
                'name': 'Contract',
                'res_model': 'tenancy.details',
                'res_id': contract_id.id,
                'view_mode': 'form,tree',
                'target': 'current'
            }
        elif self.payment_term == 'quarterly':
            self.customer_id.is_tenancy = True
            record = {
                'tenancy_id': self.customer_id.id,
                'property_id': self.property_id.id,
                'is_any_broker': self.is_any_broker,
                'broker_id': self.broker_id.id,
                'duration_id': self.duration_id.id,
                'start_date': self.start_date,
                'total_rent': self.total_rent,
                'contract_type': 'new_contract',
                'payment_term': self.payment_term,
                'rent_type': self.rent_type,
                'commission_type': self.commission_type,
                'broker_commission': self.broker_commission,
                'broker_commission_percentage': self.broker_commission_percentage,
                'is_any_deposit': self.is_any_deposit,
                'deposit_amount': self.deposit_amount,
                'agreement': self.agreement,
            }
            if service_line:
                record['extra_services_ids'] = service_line
            contract_id = self.env['tenancy.details'].create(record)

            self.property_id.write({'stage': 'on_lease'})
            return {
                'type': 'ir.actions.act_window',
                'name': 'Contract',
                'res_model': 'tenancy.details',
                'res_id': contract_id.id,
                'view_mode': 'form,tree',
                'target': 'current'
            }
        elif self.payment_term == "year":
            if not self.rent_unit == "Year":
                message = {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'type': 'info',
                        'title': ('Please select rent unit year to creare contract with payment term year'),
                        'sticky': True,
                    }
                }
                return message
            self.customer_id.is_tenancy = True
            record = {
                'tenancy_id': self.customer_id.id,
                'property_id': self.property_id.id,
                'is_any_broker': self.is_any_broker,
                'broker_id': self.broker_id.id,
                'duration_id': self.duration_id.id,
                'start_date': self.start_date,
                'total_rent': self.total_rent,
                'contract_type': 'new_contract',
                'payment_term': self.payment_term,
                'rent_type': self.rent_type,
                'commission_type': self.commission_type,
                'broker_commission': self.broker_commission,
                'broker_commission_percentage': self.broker_commission_percentage,
                'is_any_deposit': self.is_any_deposit,
                'deposit_amount': self.deposit_amount,
                'agreement': self.agreement,
            }
            if service_line:
                record['extra_services_ids'] = service_line
            contract_id = self.env['tenancy.details'].create(record)

            data = {
                'stage': 'on_lease'
            }
            self.property_id.write(data)
            return {
                'type': 'ir.actions.act_window',
                'name': 'Contract',
                'res_model': 'tenancy.details',
                'res_id': contract_id.id,
                'view_mode': 'form,tree',
                'target': 'current'
            }

    @api.onchange('from_inquiry')
    def _onchange_property_sale_inquiry(self):
        inquiry_ids = self.env['tenancy.inquiry'].search([('property_id', '=', self.property_id.id)]).mapped('id')
        for rec in self:
            if rec.from_inquiry:
                return {'domain': {'inquiry_id': [('id', 'in', inquiry_ids)]}}

    @api.onchange('inquiry_id')
    def _onchange_tenancy_inquiry(self):
        for rec in self:
            if rec.from_inquiry and rec.inquiry_id:
                rec.duration_id = rec.inquiry_id.duration_id.id
                rec.note = rec.inquiry_id.note
                rec.customer_id = rec.inquiry_id.customer_id.id

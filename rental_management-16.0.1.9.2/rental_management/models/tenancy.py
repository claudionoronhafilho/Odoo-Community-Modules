# -*- coding: utf-8 -*-
# Copyright 2020-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
import datetime
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models


class TenancyDetails(models.Model):
    _name = 'tenancy.details'
    _description = 'Information Related To customer Tenancy while Creating Contract'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'tenancy_seq'

    tenancy_seq = fields.Char(string='Sequence', required=True, readonly=True, copy=False, default=lambda self: ('New'), translate=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Currency')
    close_contract_state = fields.Boolean(string='Contract State')
    active_contract_state = fields.Boolean(string='Active State')
    is_extended = fields.Boolean(string='Extended')
    contract_type = fields.Selection([('new_contract', 'Draft'),
                                      ('running_contract', 'Running'),
                                      ('cancel_contract', 'Cancel'),
                                      ('close_contract', 'Close'),
                                      ('expire_contract', 'Expire')],
                                     string='Contract Type')

    # Tenancy Information
    tenancy_id = fields.Many2one('res.partner', string='Tenant', domain=[('user_type', '=', 'customer')])
    is_any_broker = fields.Boolean(string='Any Broker')
    broker_id = fields.Many2one('res.partner', string='Broker', domain=[('user_type', '=', 'broker')])
    commission = fields.Monetary(string='Commission ', compute='_compute_broker_commission', store=True)
    last_invoice_payment_date = fields.Date(string='Last Invoice Payment Date')
    broker_invoice_state = fields.Boolean(string='Broker  invoice State')
    broker_invoice_id = fields.Many2one('account.move', string='Bill')
    term_condition = fields.Html(string='Term and Condition')
    agreement = fields.Html(string="Agreement")
    is_any_deposit = fields.Boolean(string="Deposit")
    deposit_amount = fields.Monetary(string="Security Deposit")
    type = fields.Selection(
        [('automatic', 'Auto Create Rent Invoice Line'), ('manual', 'Manually create list of all rent invoice line')],
        default='automatic')

    # Property Information
    property_id = fields.Many2one('property.details', string='Property', domain=[('stage', '=', 'available')])
    is_extra_service = fields.Boolean(related="property_id.is_extra_service", string="Any Extra Services")
    property_landlord_id = fields.Many2one(related='property_id.landlord_id', string='Landlord', store=True)
    property_type = fields.Selection(related='property_id.type', string='Type')
    total_rent = fields.Monetary(string='Rent')
    extra_services_ids = fields.One2many('tenancy.service.line', 'tenancy_id', string="Services")

    # Time Period
    payment_term = fields.Selection([('monthly', 'Monthly'),
                                     ('full_payment', 'Full Payment'), ('quarterly', 'Quarterly'), ('year', 'Yearly')],
                                    string='Payment Term')
    duration_id = fields.Many2one('contract.duration', string='Duration')
    contract_agreement = fields.Binary(string='Contract Agreement')
    file_name = fields.Char(string='File Name', translate=True)
    month = fields.Integer(related='duration_id.month', string='Month')
    start_date = fields.Date(string='Start Date', default=fields.date.today())
    end_date = fields.Date(string='End Date', compute='_compute_end_date')

    rent_type = fields.Selection([('once', 'One Month'), ('e_rent', 'All Month')], string='Brokerage Type')
    commission_type = fields.Selection([('f', 'Fix'), ('p', 'Percentage')], string="Commission Type")
    broker_commission = fields.Monetary(string='Commission')
    broker_commission_percentage = fields.Float(string='Percentage')

    # Related Field
    rent_invoice_ids = fields.One2many('rent.invoice', 'tenancy_id', string='Invoices')

    # Tenancy Calculation
    total_tenancy = fields.Monetary(string="Total Tenancy", compute="_compute_tenancy_calculation")
    paid_tenancy = fields.Monetary(string="Paid Tenancy", compute="_compute_tenancy_calculation")
    remain_tenancy = fields.Monetary(string="Remaining Tenancy", compute="_compute_tenancy_calculation")
    rent_unit = fields.Selection(related="property_id.rent_unit")

    # Sequence Create
    @api.model
    def create(self, vals):
        if vals.get('tenancy_seq', 'New') == 'New':
            vals['tenancy_seq'] = self.env['ir.sequence'].next_by_code(
                'tenancy.details') or 'New'
        res = super(TenancyDetails, self).create(vals)
        return res

    @api.depends('start_date', 'month', 'rent_unit', 'payment_term')
    def _compute_end_date(self):
        for rec in self:
            if rec.rent_unit == "Day":
                end_date = rec.start_date + relativedelta(days=rec.month)
            elif rec.rent_unit == "Year":
                end_date = rec.start_date + relativedelta(years=rec.month) - relativedelta(days=1)
            else:
                if rec.payment_term == "year":
                    end_date = rec.start_date + relativedelta(years=rec.month) - relativedelta(days=1)
                else:
                    end_date = rec.start_date + relativedelta(months=rec.month) - relativedelta(days=1)

            rec.end_date = end_date

    @api.depends('is_any_broker', 'month')
    def _compute_broker_commission(self):
        for rec in self:
            if rec.is_any_broker:
                if rec.rent_type == 'once':
                    if rec.commission_type == 'f':
                        rec.commission = rec.broker_commission
                    else:
                        rec.commission = rec.broker_commission_percentage * rec.total_rent / 100
                else:
                    if rec.commission_type == 'f':
                        rec.commission = rec.broker_commission * rec.month
                    else:
                        rec.commission = rec.broker_commission_percentage * rec.total_rent * rec.month / 100
            else:
                rec.commission = 0

    # Smart Button
    invoice_count = fields.Integer(string='Invoice Count', compute="_compute_invoice_count")

    @api.depends('rent_invoice_ids')
    def _compute_invoice_count(self):
        for rec in self:
            count = self.env['rent.invoice'].search_count([('tenancy_id', '=', rec.id)])
            rec.invoice_count = count

    @api.depends("rent_invoice_ids")
    def _compute_tenancy_calculation(self):
        total = 0.0
        paid = 0.0
        for rec in self:
            if rec.rent_invoice_ids:
                for data in rec.rent_invoice_ids:
                    total = total + data.rent_invoice_id.amount_total
                    if data.payment_state == "paid":
                        paid = paid + data.rent_invoice_id.amount_total
            rec.total_tenancy = total
            rec.paid_tenancy = paid
            rec.remain_tenancy = total - paid

    def action_invoices(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Invoice',
            'res_model': 'rent.invoice',
            'domain': [('tenancy_id', '=', self.id)],
            'view_mode': 'tree,form',
            'target': 'current'
        }

    # Button
    def action_close_contract(self):
        self.close_contract_state = True
        self.property_id.write({'stage': 'available'})
        self.contract_type = 'close_contract'
        return True

    def action_active_contract(self):
        invoice_lines = []
        if self.is_any_broker:
            self.action_broker_invoice()
        self.contract_type = 'running_contract'
        self.active_contract_state = True
        if self.payment_term == 'monthly':
            record = {
                'product_id': self.env.ref('rental_management.property_product_1').id,
                'name': 'First Invoice of ' + self.property_id.name,
                'quantity': 1,
                'price_unit': self.total_rent
            }
            invoice_lines.append((0, 0, record))
            if self.is_any_deposit:
                deposit_record = {
                    'product_id': self.env.ref('rental_management.property_product_1').id,
                    'name': 'Deposit of ' + self.property_id.name,
                    'quantity': 1,
                    'price_unit': self.deposit_amount
                }
                invoice_lines.append((0, 0, deposit_record))
            for rec in self:
                desc = ""
                if rec.is_extra_service:
                    for line in rec.extra_services_ids:
                        if line.service_type == "once":
                            desc = "Once"
                        if line.service_type == "monthly":
                            desc = "Monthly"
                        service_invoice_record = {
                            'product_id': line.service_id.id,
                            'name': desc,
                            'quantity': 1,
                            'price_unit': line.price
                        }
                        invoice_lines.append((0, 0, service_invoice_record))
            data = {
                'partner_id': self.tenancy_id.id,
                'move_type': 'out_invoice',
                'invoice_date': fields.Date.today(),
                'invoice_line_ids': invoice_lines
            }
            invoice_id = self.env['account.move'].sudo().create(data)
            invoice_id.tenancy_id = self.id
            invoice_id.action_post()
            self.last_invoice_payment_date = invoice_id.invoice_date
            self.action_send_active_contract()
            amount_total = invoice_id.amount_total
            rent_invoice = {
                'tenancy_id': self.id,
                'type': 'rent',
                'invoice_date': fields.Date.today(),
                'description': 'First Rent',
                'rent_invoice_id': invoice_id.id,
                'amount': amount_total,
                'rent_amount': self.total_rent
            }
            if self.is_any_deposit:
                rent_invoice['description'] = 'First Rent + Deposit'
            else:
                rent_invoice['description'] = 'First Rent'
            self.env['rent.invoice'].create(rent_invoice)
        elif self.payment_term == 'quarterly':
            record = {
                'product_id': self.env.ref('rental_management.property_product_1').id,
                'name': 'First Quarter Invoice of ' + self.property_id.name,
                'quantity': 1,
                'price_unit': self.total_rent * 3
            }
            invoice_lines.append((0, 0, record))
            if self.is_any_deposit:
                deposit_record = {
                    'product_id': self.env.ref('rental_management.property_product_1').id,
                    'name': 'Deposit of ' + self.property_id.name,
                    'quantity': 1,
                    'price_unit': self.deposit_amount
                }
                invoice_lines.append((0, 0, deposit_record))
            for rec in self:
                desc = ""
                if rec.is_extra_service:
                    for line in rec.extra_services_ids:
                        if line.service_type == "once":
                            desc = "Once"
                            service_invoice_record = {
                                'product_id': line.service_id.id,
                                'name': desc,
                                'quantity': 1,
                                'price_unit': line.price
                            }
                            invoice_lines.append((0, 0, service_invoice_record))
                        if line.service_type == "monthly":
                            desc = "Monthly"
                            service_invoice_record = {
                                'product_id': line.service_id.id,
                                'name': desc,
                                'quantity': 3,
                                'price_unit': line.price
                            }
                            invoice_lines.append((0, 0, service_invoice_record))
            data = {
                'partner_id': self.tenancy_id.id,
                'move_type': 'out_invoice',
                'invoice_date': fields.Date.today(),
                'invoice_line_ids': invoice_lines
            }
            invoice_id = self.env['account.move'].sudo().create(data)
            invoice_id.tenancy_id = self.id
            invoice_id.action_post()
            self.last_invoice_payment_date = invoice_id.invoice_date
            self.action_send_active_contract()
            amount_total = invoice_id.amount_total
            rent_invoice = {
                'tenancy_id': self.id,
                'type': 'rent',
                'invoice_date': fields.Date.today(),
                'description': 'First Quarter Rent',
                'rent_invoice_id': invoice_id.id,
                'amount': amount_total,
                'rent_amount': self.total_rent * 3
            }
            if self.is_any_deposit:
                rent_invoice['description'] = 'First Quarter Rent + Deposit'
            else:
                rent_invoice['description'] = 'First Quarter Rent'
            self.env['rent.invoice'].create(rent_invoice)
        elif self.payment_term == 'year':
            if self.is_any_deposit:
                deposit_record = {
                    'product_id': self.env.ref('rental_management.property_product_1').id,
                    'name': 'Deposit of ' + self.property_id.name,
                    'quantity': 1,
                    'price_unit': self.deposit_amount
                }
                invoice_lines.append((0, 0, deposit_record))
            for rec in self:
                desc = ""
                if rec.is_extra_service:
                    for line in rec.extra_services_ids:
                        if line.service_type == "once":
                            desc = "Once"
                            service_invoice_record = {
                                'product_id': line.service_id.id,
                                'name': desc,
                                'quantity': 1,
                                'price_unit': line.price
                            }
                            invoice_lines.append((0, 0, service_invoice_record))
                        if line.service_type == "monthly":
                            desc = "Monthly"
                            service_invoice_record = {
                                'product_id': line.service_id.id,
                                'name': desc,
                                'quantity': 12,
                                'price_unit': line.price
                            }
                            invoice_lines.append((0, 0, service_invoice_record))
            if invoice_lines:
                data = {
                    'partner_id': self.tenancy_id.id,
                    'move_type': 'out_invoice',
                    'invoice_date': fields.Date.today(),
                    'invoice_line_ids': invoice_lines,
                    'tenancy_id': self.id
                }
                inv_id = self.env['account.move'].sudo().create(data)
                inv_id.action_post()
                rent_invoice = {
                    'tenancy_id': self.id,
                    'type': 'rent',
                    'invoice_date': inv_id.invoice_date,
                    'description': 'First Yearly Rent',
                    'rent_invoice_id': inv_id.id,
                    'amount': inv_id.amount_total,
                    'rent_amount': inv_id.amount_total
                }
                if self.is_any_deposit and self.is_extra_service:
                    rent_invoice['description'] = "Deposit + Extra Service"
                elif self.is_any_deposit:
                    rent_invoice['description'] = "Deposit Amount"
                elif self.is_extra_service:
                    rent_invoice['description'] = "Extra Service"
                self.env['rent.invoice'].create(rent_invoice)
            line = []
            record = {
                'product_id': self.env.ref('rental_management.property_product_1').id,
                'name': 'First Year Invoice of ' + self.property_id.name,
                'quantity': 1,
                'price_unit': self.total_rent
            }
            line.append((0, 0, record))
            data = {
                'partner_id': self.tenancy_id.id,
                'move_type': 'out_invoice',
                'invoice_date': fields.Date.today(),
                'invoice_line_ids': line,
                'tenancy_id': self.id
            }
            invoice = self.env['account.move'].sudo().create(data)
            invoice.action_post()
            self.last_invoice_payment_date = invoice.invoice_date
            rent_invoice = {
                'tenancy_id': self.id,
                'is_yearly': True,
                'type': 'rent',
                'invoice_date': invoice.invoice_date,
                'description': 'First Year Rent',
                'rent_invoice_id': invoice.id,
                'amount': invoice.amount_total,
                'rent_amount': self.total_rent * 12
            }
            self.env['rent.invoice'].create(rent_invoice)
            self.action_send_active_contract()

    def action_cancel_contract(self):
        self.close_contract_state = True
        self.property_id.write({'stage': 'available'})
        self.contract_type = 'cancel_contract'

    def action_send_active_contract(self):
        mail_template = self.env.ref('rental_management.active_contract_mail_template')
        if mail_template:
            mail_template.send_mail(self.id, force_send=True)

    def action_send_tenancy_reminder(self):
        mail_template = self.env.ref('rental_management.tenancy_reminder_mail_template')
        if mail_template:
            mail_template.send_mail(self.id, force_send=True)

    def action_broker_invoice(self):
        record = {
            'product_id': self.env.ref('rental_management.property_product_1').id,
            'name': 'Brokerage of ' + self.property_id.name,
            'quantity': 1,
            'price_unit': self.commission
        }
        invoice_lines = [(0, 0, record)]
        data = {
            'partner_id': self.broker_id.id,
            'move_type': 'in_invoice',
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': invoice_lines
        }
        invoice_id = self.env['account.move'].sudo().create(data)
        invoice_id.tenancy_id = self.id
        invoice_id.action_post()
        self.broker_invoice_state = True
        self.broker_invoice_id = invoice_id.id
        return True

    @api.model
    def tenancy_recurring_invoice(self):
        # today_date = datetime.date(2023, 8, 1)
        today_date = fields.Date.today()
        reminder_days = self.env['ir.config_parameter'].sudo().get_param('rental_management.reminder_days')
        tenancy_contracts = self.env['tenancy.details'].sudo().search(
            [('contract_type', '=', 'running_contract'), ('payment_term', '=', 'monthly'), ('rent_unit', '=', 'Month'),
             ('type', '=', 'automatic')])
        for rec in tenancy_contracts:
            if rec.contract_type == 'running_contract' and rec.payment_term == 'monthly':
                if today_date < rec.end_date:
                    invoice_date = rec.last_invoice_payment_date + relativedelta(months=1)
                    next_invoice_date = rec.last_invoice_payment_date + relativedelta(months=1) - relativedelta(
                        days=int(reminder_days))
                    if today_date == next_invoice_date:
                        record = {
                            'product_id': self.env.ref('rental_management.property_product_1').id,
                            'name': 'Installment of ' + rec.property_id.name,
                            'quantity': 1,
                            'price_unit': rec.total_rent
                        }
                        invoice_lines = [(0, 0, record)]
                        if rec.is_extra_service:
                            for line in rec.extra_services_ids:
                                if line.service_type == "monthly":
                                    desc = "Monthly"
                                    service_invoice_record = {
                                        'product_id': line.service_id.id,
                                        'name': desc,
                                        'quantity': 1,
                                        'price_unit': line.price
                                    }
                                    invoice_lines.append((0, 0, service_invoice_record))
                        data = {
                            'partner_id': rec.tenancy_id.id,
                            'move_type': 'out_invoice',
                            'invoice_date': invoice_date,
                            'invoice_line_ids': invoice_lines
                        }
                        invoice_id = self.env['account.move'].sudo().create(data)
                        invoice_id.tenancy_id = rec.id
                        invoice_id.action_post()
                        rec.last_invoice_payment_date = invoice_id.invoice_date
                        rent_invoice = {
                            'tenancy_id': rec.id,
                            'type': 'rent',
                            'invoice_date': invoice_date,
                            'description': 'Installment of ' + rec.property_id.name,
                            'rent_invoice_id': invoice_id.id,
                            'amount': invoice_id.amount_total,
                            'rent_amount': self.total_rent
                        }
                        self.env['rent.invoice'].create(rent_invoice)
                        rec.action_send_tenancy_reminder()

    @api.model
    def tenancy_expire(self):
        today_date = fields.Date.today()
        tenancy_contracts = self.env['tenancy.details'].sudo().search(
            [('contract_type', '=', 'running_contract')])
        for rec in tenancy_contracts:
            if rec.contract_type == 'running_contract' and today_date > rec.end_date:
                rec.contract_type = 'expire_contract'

    @api.model
    def tenancy_recurring_quarterly_invoice(self):
        today_date = fields.Date.today()
        # today_date = datetime.date(2024, 4, 1)
        reminder_days = self.env['ir.config_parameter'].sudo().get_param('rental_management.reminder_days')
        tenancy_contracts = self.env['tenancy.details'].sudo().search(
            [('contract_type', '=', 'running_contract'), ('payment_term', '=', 'quarterly'),
             ('type', '=', 'automatic'), ('rent_unit', '=', 'Month')])
        for rec in tenancy_contracts:
            if rec.contract_type == 'running_contract' and rec.payment_term == 'quarterly':
                if today_date < rec.end_date:
                    invoice_date = rec.last_invoice_payment_date + relativedelta(months=3)
                    next_next_invoice_date = invoice_date + relativedelta(months=3)
                    next_invoice_date = rec.last_invoice_payment_date + relativedelta(months=3) - relativedelta(
                        days=int(reminder_days))
                    if rec.end_date < next_next_invoice_date:
                        delta = relativedelta(next_next_invoice_date, rec.end_date)
                        diff = delta.months
                    else:
                        diff = 0
                    if today_date == next_invoice_date:
                        record = {
                            'product_id': self.env.ref('rental_management.property_product_1').id,
                            'name': 'Quarterly Installment of ' + rec.property_id.name,
                            'quantity': 1,
                            'price_unit': rec.total_rent * (3 - diff)
                        }
                        invoice_lines = [(0, 0, record)]
                        if rec.is_extra_service:
                            for line in rec.extra_services_ids:
                                if line.service_type == "monthly":
                                    desc = "Quarterly Service"
                                    service_invoice_record = {
                                        'product_id': line.service_id.id,
                                        'name': desc,
                                        'quantity': 1,
                                        'price_unit': line.price * (3 - diff)
                                    }
                                    invoice_lines.append((0, 0, service_invoice_record))
                        data = {
                            'partner_id': rec.tenancy_id.id,
                            'move_type': 'out_invoice',
                            'invoice_date': invoice_date,
                            'invoice_line_ids': invoice_lines
                        }
                        invoice_id = self.env['account.move'].sudo().create(data)
                        invoice_id.tenancy_id = rec.id
                        invoice_id.action_post()
                        rec.last_invoice_payment_date = invoice_id.invoice_date
                        rent_invoice = {
                            'tenancy_id': rec.id,
                            'type': 'rent',
                            'invoice_date': invoice_date,
                            'description': 'Quarterly Installment of ' + rec.property_id.name,
                            'rent_invoice_id': invoice_id.id,
                            'amount': invoice_id.amount_total,
                            'rent_amount': self.total_rent * (3 - diff)
                        }
                        self.env['rent.invoice'].create(rent_invoice)
                        rec.action_send_tenancy_reminder()

    @api.model
    def tenancy_yearly_invoice(self):
        today_date = fields.Date.today()
        # today_date = datetime.date(2024, 7, 1)
        reminder_days = self.env['ir.config_parameter'].sudo().get_param('rental_management.reminder_days')
        tenancy_contracts = self.env['tenancy.details'].sudo().search(
            [('contract_type', '=', 'running_contract'), ('type', '=', 'automatic'), ('payment_term', '=', 'year'),
             ('rent_unit', '=', 'Year')])
        for rec in tenancy_contracts:
            if today_date < rec.end_date:
                invoice_date = rec.last_invoice_payment_date + relativedelta(years=1)
                next_invoice_date = rec.last_invoice_payment_date + relativedelta(years=1) - relativedelta(
                    days=int(reminder_days))
                if today_date == next_invoice_date:
                    record = {
                        'product_id': self.env.ref('rental_management.property_product_1').id,
                        'name': 'Yearly Installment of ' + rec.property_id.name,
                        'quantity': 1,
                        'price_unit': rec.total_rent
                    }
                    invoice_lines = [(0, 0, record)]
                    if rec.is_extra_service:
                        for line in rec.extra_services_ids:
                            if line.service_type == "monthly":
                                desc = "Monthly"
                                service_invoice_record = {
                                    'product_id': line.service_id.id,
                                    'name': desc,
                                    'quantity': 12,
                                    'price_unit': line.price
                                }
                                invoice_lines.append((0, 0, service_invoice_record))
                    data = {
                        'partner_id': rec.tenancy_id.id,
                        'move_type': 'out_invoice',
                        'invoice_date': invoice_date,
                        'invoice_line_ids': invoice_lines
                    }
                    invoice_id = self.env['account.move'].sudo().create(data)
                    invoice_id.tenancy_id = rec.id
                    invoice_id.action_post()
                    rec.last_invoice_payment_date = invoice_id.invoice_date
                    rent_invoice = {
                        'tenancy_id': rec.id,
                        'type': 'rent',
                        'invoice_date': invoice_date,
                        'description': 'Installment of ' + rec.property_id.name,
                        'rent_invoice_id': invoice_id.id,
                        'amount': invoice_id.amount_total,
                        'rent_amount': self.total_rent
                    }
                    self.env['rent.invoice'].create(rent_invoice)
                    rec.action_send_tenancy_reminder()

    @api.model
    def tenancy_manual_invoice(self):
        today_date = fields.Date.today()
        # today_date = datetime.date(2023, 8, 2)
        reminder_days = self.env['ir.config_parameter'].sudo().get_param('rental_management.reminder_days')
        tenancy_contracts = self.env['tenancy.details'].sudo().search(
            [('contract_type', '=', 'running_contract'), ('type', '=', 'manual')])
        for data in tenancy_contracts:
            for rec in data.rent_invoice_ids:
                if not rec.rent_invoice_id:
                    invoice_date = rec.invoice_date - relativedelta(days=int(reminder_days))
                    if today_date == invoice_date:
                        rec.action_create_invoice()
            data.action_send_tenancy_reminder()


class ContractDuration(models.Model):
    _name = 'contract.duration'
    _description = 'Contract Duration and Month'
    _rec_name = 'duration'

    duration = fields.Char(string='Duration', required=True, translate=True)
    month = fields.Integer(string='Unit')
    rent_unit = fields.Selection([('Day', "Day"),
                                  ('Month', "Month"),
                                  ('Year', "Year")],
                                 default='Month',
                                 string="Rent Unit")


class TenancyExtraServiceLine(models.Model):
    _name = "tenancy.service.line"
    _description = "Tenancy Service Line"

    service_id = fields.Many2one('product.product', string="Service", domain=[('is_extra_service_product', '=', True)])
    price = fields.Float(related="service_id.lst_price", string="Cost")
    service_type = fields.Selection([('once', 'Once'), ('monthly', 'Monthly')], string="Type", default="once")
    tenancy_id = fields.Many2one('tenancy.details', string="Tenancies")
    from_contract = fields.Boolean()

    def action_create_service_invoice(self):
        self.from_contract = True
        record = {
            'product_id': self.service_id.id,
            'name': "Extra Added Service",
            'quantity': 1,
            'price_unit': self.service_id.lst_price
        }
        invoice_lines = [(0, 0, record)]
        data = {
            'partner_id': self.tenancy_id.tenancy_id.id,
            'move_type': 'out_invoice',
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': invoice_lines
        }
        invoice_id = self.env['account.move'].sudo().create(data)
        invoice_id.tenancy_id = self.tenancy_id.id
        invoice_id.action_post()
        rent_invoice = {
            'tenancy_id': self.tenancy_id.id,
            'type': 'maintenance',
            'amount': self.service_id.lst_price,
            'invoice_date': fields.Date.today(),
            'description': 'New Service',
            'rent_invoice_id': invoice_id.id
        }
        self.env['rent.invoice'].create(rent_invoice)


class AgreementTemplate(models.Model):
    _name = "agreement.template"
    _description = "Agreement Template"

    name = fields.Char(string="Title", translate=True)
    agreement = fields.Html(string="Agreement")

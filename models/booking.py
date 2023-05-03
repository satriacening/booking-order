# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from datetime import datetime, timedelta


from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ServiceTeam(models.Model):

    _name = "service.team"
    _rec_name = "team_name"
    _description = "Service Team"

    team_name = fields.Char(string="Team Name", required=True)
    team_leader = fields.Many2one('res.users', string='Team Leader', required=True)
    team_members = fields.Many2many('res.users', string='Team Members')


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    is_booking_order = fields.Boolean(string='Is booking order', default=True)
    team = fields.Many2one('service.team', string='Team')
    team_leader = fields.Many2one('res.users', string='Team Leader')
    team_members = fields.Many2many('res.users', string='Team Members')
    booking_start = fields.Datetime(string="Booking Start")
    booking_end = fields.Datetime(string="Booking End")
    overlap_check = fields.Boolean(default=False)
    work_order = fields.Many2one('work.order', string='Work Order')

    def func_check(self):
        print("check is triggered")
        planned_list =[]
        working_order = self.env['work.order'].search([('planned_start', '!=', None),('state', '!=', 'cancelled')])
        for i in working_order:
            planned_start = datetime.strptime(i.planned_start, '%Y-%m-%d %H:%M:%S')
            planned_end = datetime.strptime(i.planned_end, '%Y-%m-%d %H:%M:%S')
            while planned_start <= planned_end:
                planned_list.append((planned_start).strftime("%d%m%Y"))
                planned_start += timedelta(days=1)

        booking_start = datetime.strptime(self.booking_start, '%Y-%m-%d %H:%M:%S')
        booking_end = datetime.strptime(self.booking_end, '%Y-%m-%d %H:%M:%S')
        booking_list = []

        while booking_start <= booking_end:
            booking_list.append((booking_start).strftime("%d%m%Y"))
            booking_start += timedelta(days=1)
        exist = False
        for i in booking_list:
            if i in planned_list:
                exist = True
                print("exist")
                self.overlap_check = True
                print ("dalam check", self.overlap_check)
                raise UserError(_('Team already has work order during that period on' + self.name))
        if not exist:
            raise UserError(_('Team is available for booking'))

    @api.onchange('team')
    def onchange_team(self):
        for rec in self:
            rec.team_leader = rec.team.team_leader
            rec.team_members = rec.team.team_members

    @api.multi
    def action_confirm(self):
        print('dalam confirm', self.overlap_check)
        if self.overlap_check:
            raise UserError(_('Team already has work order during that period on' + self.name))

        for order in self:
            order.state = 'sale'
            order.confirmation_date = fields.Datetime.now()
            if self.env.context.get('send_email'):
                order.force_quotation_send()
            order.order_line._action_procurement_create()

        if self.env['ir.values'].get_default('sale.config.settings', 'auto_done_setting'):
            self.action_done()

        # edit button confirm sale
        ref = self.id
        members = []
        for i in self.team_members:
            members.append(i.id)

        seq = self.env['ir.sequence'].next_by_code('work.order') or _('New')
        for rec in self:
            values = {
                    'wo_number': seq,
                    'team': self.team.id,
                    'team_leader': self.team_leader.id,
                    'planned_start': self.booking_start,
                    'planned_end': self.booking_end,
                    'date_start': self.booking_start,
                    'date_end': self.booking_end,
                    'state': 'pending',
                    'reference': ref,
                    'team_members': [(6,0,rec.team_members.ids)],
                }
            self.env['work.order'].create(values)

        wo = self.env['work.order'].search([('reference', '=', ref)])

        for i in wo:
            self.work_order = i.id

        # en code from edit button sale

        return True

    @api.multi
    def action_view_work_order(self):
        action = (self.env.ref("action_booking_order_work_order").sudo().read()[0])
        lines = self.mapped("line_ids")
        if len(lines) > 1:
            action["domain"] = [("", "in", lines.ids)]
        elif lines:
            action["views"] = [(self.env.ref("id form view").id, "form")]
            action[" res_id"] = lines.ids[0]
        return action


class WorkOrder(models.Model):
    _name = "work.order"
    _rec_name = "wo_number"
    _description = "Work Order"

    wo_number = fields.Char(string='WO Number', compute='', readonly=True, default=lambda self: _('New'))
    reference = fields.Many2one('sale.order', string='Booking Order Reference', readonly=True, compute='')
    team = fields.Many2one('service.team', string='Team', required=True)
    team_leader = fields.Many2one('res.users', string='Team Leader', required=True)
    team_members = fields.Many2many('res.users', string='Team Members', store=True)
    planned_start = fields.Datetime(string='Planned Start', required=True)
    planned_end = fields.Datetime(string='Planned End', required=True)
    date_start = fields.Datetime(string='Date Start', readonly=True)
    date_end = fields.Datetime(string='Date End', readonly=True)
    state = fields.Selection([('pending', 'Pending'), ('in_progress', 'In Progress'),('done', 'Done'),('cancelled', 'Cancelled')], default='pending')
    notes = fields.Text(string='Note')

    @api.model
    def create(self, vals):
        vals['wo_number'] = self.env['ir.sequence'].next_by_code('work.order') or _('New')

        result = super(WorkOrder, self).create(vals)
        return result

    @api.multi
    def func_start_work(self):
        self.date_start = fields.Datetime.now()
        return self.write({'state': 'in_progress'})

    def func_end_work(self):
        self.date_end = fields.Datetime.now()
        return self.write({'state': 'done'})

    def func_reset(self):
        self.date_start = None
        return self.write({'state': 'pending'})

    @api.onchange('team')
    def onchange_team(self):
        for rec in self:

            rec.team_leader = rec.team.team_leader
            rec.team_members = rec.team.team_members

    @api.multi
    def write(self, vals):
        res = super(WorkOrder, self).write(vals)
        return res


class OrderCancelReason(models.Model):
    _name = 'cancel.reason'
    _description = 'Cancel Reason'

    name = fields.Char('Reason', required=True, translate=True)
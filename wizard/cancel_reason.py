# -*- coding: utf-8 -*-
# Author: Guewen Baconnier
# Copyright 2013 Camptocamp SA
# Copyright 2016 Serpent Consulting Services Pvt. Ltd.
# (http://www.serpentcs.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _

class WorkOrderCancel(models.TransientModel):

    _name = 'work.order.cancel'
    _description = __doc__

    reason_note = fields.Text(required=True)

    @api.multi
    def confirm_cancel(self):
        act_close = {'type': 'ir.actions.act_window_close'}
        work_ids = self._context.get('active_ids')
        if work_ids is None:
            return act_close
        assert len(work_ids) == 1, "Only 1 work ID expected"
        work = self.env['work.order'].browse(work_ids)
        work.notes = self.reason_note
        work.state = 'cancelled'
        return act_close

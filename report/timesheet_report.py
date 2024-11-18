# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Kavya Raveendran (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import api, fields, models
from collections import defaultdict

class ReportTimesheet(models.AbstractModel):
    _name = 'report.timesheets_by_employee.report_timesheets'
    _description = 'Timesheet Report'

    def get_timesheets(self, docs):
        domain = [('user_id', '=', docs.user_id[0].id)]
        if docs.from_date:
            domain.append(('date', '>=', docs.from_date))
        if docs.to_date:
            domain.append(('date', '<=', docs.to_date))
            
        record = self.env['account.analytic.line'].search(domain, order='project_id, task_id, date')
        
        timesheet_data = {
            'projects': defaultdict(lambda: {'tasks': defaultdict(lambda: {'entries': [], 'subtotal': 0.0}), 'subtotal': 0.0}),
            'total': 0.0
        }
        
        for rec in record:
            hours = int(rec.unit_amount)
            minutes = int((rec.unit_amount - hours) * 60)
            duration_str = f"{hours:02d}:{minutes:02d}"
            
            project_name = rec.project_id.name or 'No Project'
            task_name = rec.task_id.name or 'No Task'
            
            entry = {
                'date': rec.date,
                'description': rec.name or '',
                'duration': duration_str,
                'hours': rec.unit_amount
            }
            
            timesheet_data['projects'][project_name]['tasks'][task_name]['entries'].append(entry)
            timesheet_data['projects'][project_name]['tasks'][task_name]['subtotal'] += rec.unit_amount
            timesheet_data['projects'][project_name]['subtotal'] += rec.unit_amount
            timesheet_data['total'] += rec.unit_amount
        
        total_hours = int(timesheet_data['total'])
        total_minutes = int((timesheet_data['total'] - total_hours) * 60)
        timesheet_data['total'] = f"{total_hours:02d}:{total_minutes:02d}"
        
        return timesheet_data

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['timesheet.report'].browse(self.env.context.get('active_id'))
        identification = []
        for rec in self.env['hr.employee'].search([('user_id', '=', docs.user_id[0].id)]):
            identification.append({
                'id': rec.id,
                'name': rec.name
            })
            
        period = None
        if docs.from_date and docs.to_date:
            period = f"From {docs.from_date} To {docs.to_date}"
        elif docs.from_date:
            period = f"From {docs.from_date}"
        elif docs.to_date:
            period = f"To {docs.to_date}"
            
        timesheet_data = self.get_timesheets(docs)
        
        return {
            'doc_ids': self.ids,
            'docs': docs,
            'identification': identification,
            'period': period,
            'timesheet_data': timesheet_data,
        }

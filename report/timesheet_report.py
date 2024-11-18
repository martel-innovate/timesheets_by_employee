from odoo import api, fields, models
from collections import defaultdict
from datetime import datetime

class ReportTimesheet(models.AbstractModel):
    _name = 'report.timesheets_by_employee.report_timesheets'
    _description = 'Timesheet Report'

    def format_time_24h(self, hours):
        """Convert float hours to 24h format string"""
        total_minutes = int(hours * 60)
        hours = total_minutes // 60
        minutes = total_minutes % 60
        return f"{hours:02d}:{minutes:02d}"

    def get_timesheets(self, docs):
        domain = [('user_id', '=', docs.user_id[0].id)]
        if docs.from_date:
            domain.append(('date', '>=', docs.from_date))
        if docs.to_date:
            domain.append(('date', '<=', docs.to_date))
            
        record = self.env['account.analytic.line'].search(domain, order='project_id, task_id, date')
        
        timesheet_data = {
            'projects': defaultdict(lambda: {'tasks': defaultdict(lambda: {'entries': [], 'subtotal': 0.0}), 'subtotal': 0.0}),
            'total': 0.0,
            'total_hours_display': '00:00'
        }
        
        for rec in record:
            project_name = rec.project_id.name or 'No Project'
            task_name = rec.task_id.name or 'No Task'
            
            entry = {
                'date': rec.date,
                'description': rec.name or '',
                'duration': self.format_time_24h(rec.unit_amount),
                'hours': rec.unit_amount
            }
            
            timesheet_data['projects'][project_name]['tasks'][task_name]['entries'].append(entry)
            timesheet_data['projects'][project_name]['tasks'][task_name]['subtotal'] += rec.unit_amount
            timesheet_data['projects'][project_name]['subtotal'] += rec.unit_amount
            timesheet_data['total'] += rec.unit_amount

        # Format subtotals
        for project in timesheet_data['projects'].values():
            project['subtotal_display'] = self.format_time_24h(project['subtotal'])
            for task in project['tasks'].values():
                task['subtotal_display'] = self.format_time_24h(task['subtotal'])
        
        timesheet_data['total_hours_display'] = self.format_time_24h(timesheet_data['total'])
        
        return timesheet_data

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['timesheet.report'].browse(self.env.context.get('active_id'))
        company = self.env.company

        employee = self.env['hr.employee'].search([('user_id', '=', docs.user_id[0].id)], limit=1)
        
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
            'doc_model':'timesheet.report',
            'docs': docs,
            'employee': employee,
            'period': period,
            'timesheet_data': timesheet_data,
            'company': company,
            'o': docs,
        }

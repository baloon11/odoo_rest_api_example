# -*- coding: utf-8 -*-

from odoo import models, fields, api


class DeleteLog(models.Model):
    _name = 'kiiver_mobile.delete_log'

    user_id = fields.Many2one('res.users', string='User', required=True)
    project_id = fields.Many2one('project.project', string='Project', required=True)
    datetime = fields.Datetime('Date', default=fields.Datetime.now)


class CustomProject(models.Model):
    _inherit = 'project.project'

    @api.model
    def create(self, vals):
        default_stages_ids = self.env['project.task.type'].search([('name', 'in', ["Future", "In progress"])]).ids
        project = super(CustomProject, self).create(vals)
        project.write({'type_ids': [(6, 0, default_stages_ids)]})
        return project

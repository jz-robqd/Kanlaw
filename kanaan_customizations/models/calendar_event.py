from odoo import api, fields, models


class CalendarEvent(models.Model):
    _inherit = "calendar.event"

    kanaan_lawyer_id = fields.Many2one(
        "res.users",
        string="Lawyer",
        compute="_compute_kanaan_lawyer",
        store=True,
        index=True,
        help="Lawyer responsible for this hearing, used to colour the Hearings calendar. "
             "Taken from (1) the activity's assignee, (2) any attendee other than the "
             "organiser, (3) the case's assignees, else the organiser.",
    )

    @api.depends("user_id", "partner_ids", "activity_ids.user_id", "res_model", "res_id")
    def _compute_kanaan_lawyer(self):
        Task = self.env["project.task"].sudo()
        for event in self:
            organizer = event.user_id
            lawyer = event.activity_ids.user_id.filtered(lambda u: u != organizer)[:1]
            if not lawyer:
                others = event.partner_ids - organizer.partner_id
                lawyer = others.sudo().user_ids.filtered(lambda u: not u.share)[:1]
            if not lawyer and event.res_model == "project.task" and event.res_id:
                task = Task.browse(event.res_id).exists()
                lawyer = (task.user_ids - organizer)[:1] or task.user_ids[:1]
            event.kanaan_lawyer_id = lawyer or organizer

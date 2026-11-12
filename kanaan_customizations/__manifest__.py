{
    "name": "Kanaan Legal – Customizations",
    "version": "19.0.1.0.0",
    "summary": "Counterparty contacts, hearing colours per lawyer, file number on documents, timesheet add-line on top",
    "author": "Roboqode",
    "license": "LGPL-3",
    "depends": ["web", "contacts", "project", "hr_timesheet", "calendar", "documents"],
    "data": [
        "security/kanaan_security.xml",
        "views/res_partner_views.xml",
        "views/calendar_event_views.xml",
        "views/project_task_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "kanaan_customizations/static/src/timesheet_add_top/*",
        ],
    },
    "post_init_hook": "post_init_hook",
    "installable": True,
    "application": False,
}

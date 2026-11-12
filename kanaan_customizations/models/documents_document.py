from lxml import etree

from odoo import api, fields, models

from .kanaan_config import get_file_number_field


class DocumentsDocument(models.Model):
    _inherit = "documents.document"

    kanaan_case_id = fields.Many2one(
        "project.task", string="Case", compute="_compute_kanaan_case", store=True, index=True)
    kanaan_file_number = fields.Char(
        string="File Number", compute="_compute_kanaan_case", store=True, index=True)

    @api.depends("res_model", "res_id")
    def _compute_kanaan_case(self):
        file_no = get_file_number_field(self.env)
        Task = self.env["project.task"].sudo()
        for doc in self:
            task = Task.browse(doc.res_id).exists() if doc.res_model == "project.task" and doc.res_id else Task
            doc.kanaan_case_id = task
            value = task[file_no] if task and file_no else False
            if isinstance(value, models.BaseModel):
                value = value.display_name
            doc.kanaan_file_number = str(value) if value not in (False, None) else False

    @api.model
    def _get_view(self, view_id=None, view_type="form", **options):
        # Injected in Python rather than XML inheritance so it doesn't depend on
        # the Documents (Enterprise) view xmlids, which change between versions.
        arch, view = super()._get_view(view_id, view_type, **options)
        if view_type == "list" and not arch.xpath("//field[@name='kanaan_file_number']"):
            new = [etree.Element("field", name="kanaan_file_number", optional="show"),
                   etree.Element("field", name="kanaan_case_id", optional="show")]
            anchor = arch.xpath("//field[@name='owner_id']")
            for node in new:
                if anchor:
                    anchor[0].addprevious(node)
                else:
                    arch.append(node)
        elif view_type == "search" and not arch.xpath("//field[@name='kanaan_file_number']"):
            new = [
                etree.Element("field", name="kanaan_file_number"),
                etree.Element("field", name="kanaan_case_id"),
                etree.Element("filter", name="kanaan_groupby_case", string="Case",
                              context="{'group_by': 'kanaan_case_id'}"),
                etree.Element("filter", name="kanaan_groupby_file_number", string="File Number",
                              context="{'group_by': 'kanaan_file_number'}"),
            ]
            panel = arch.find("searchpanel")
            for node in new:
                if panel is not None:
                    panel.addprevious(node)
                else:
                    arch.append(node)
        return arch, view

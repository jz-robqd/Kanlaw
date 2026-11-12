from odoo import api, models

from .kanaan_config import get_file_number_field, get_party_fields
from .res_partner import LOOKUP_CTX

PARTY_CTX_KEYS = f"'{LOOKUP_CTX}': True, 'default_kanaan_is_counterparty': True"
PARTY_OPTIONS = "'no_create_edit': True, 'no_open': True"


def _merge_dict_attr(node, attr, extra):
    """Add keys to a dict-literal attribute (context / options) on a view node."""
    current = (node.get(attr) or "").strip()
    if current.startswith("{") and current.endswith("}"):
        inner = current[1:-1].strip()
        node.set(attr, "{%s%s}" % (extra, (", " + inner) if inner else ""))
    elif not current:
        node.set(attr, "{%s}" % extra)
    # anything else (a variable/expression) is left untouched


class KanaanPartyFieldsMixin(models.AbstractModel):
    _name = "kanaan.party.fields.mixin"
    _description = "Kanaan: wire Party fields to counterparty lookup"

    @api.model
    def _get_view(self, view_id=None, view_type="form", **options):
        arch, view = super()._get_view(view_id, view_type, **options)
        if view_type in ("form", "list"):
            for fname in get_party_fields(self.env, self._name):
                for node in arch.xpath(f"//field[@name='{fname}']"):
                    _merge_dict_attr(node, "context", PARTY_CTX_KEYS)
                    _merge_dict_attr(node, "options", PARTY_OPTIONS)
        return arch, view


class ProjectProject(models.Model):
    _name = "project.project"
    _inherit = ["project.project", "kanaan.party.fields.mixin"]


class ProjectTask(models.Model):
    _name = "project.task"
    _inherit = ["project.task", "kanaan.party.fields.mixin"]

    def write(self, vals):
        res = super().write(vals)
        file_no = get_file_number_field(self.env)
        if file_no and file_no in vals:
            docs = self.env["documents.document"].sudo().search([
                ("res_model", "=", "project.task"), ("res_id", "in", self.ids)])
            docs._compute_kanaan_case()
        if "user_ids" in vals:
            events = self.env["calendar.event"].sudo().search([
                ("res_model", "=", "project.task"), ("res_id", "in", self.ids)])
            events._compute_kanaan_lawyer()
        return res

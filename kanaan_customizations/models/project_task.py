import re

from odoo import api, models

from .kanaan_config import PARTY_LABEL, get_file_number_field, get_party_fields
from .res_partner import LOOKUP_CTX

PARTY_CTX_KEYS = f"'{LOOKUP_CTX}': True, 'default_kanaan_is_counterparty': True"
PARTY_OPTIONS = "'no_create_edit': True, 'no_open': True"
PARTY_DOMAIN = "('kanaan_is_counterparty', '=', True)"
# Partner fields sitting in a tab like "Counterparty Docs and Info" are treated as Party fields
PARTY_PAGE = re.compile(r"counter.?part|opponent", re.I)
NOT_PARTY = {"partner_id", "message_partner_ids", "commercial_partner_id"}


def _merge_dict_attr(node, attr, extra):
    """Add keys to a dict-literal attribute (context / options) on a view node."""
    current = (node.get(attr) or "").strip()
    if current.startswith("{") and current.endswith("}"):
        inner = current[1:-1].strip()
        if extra.split(":")[0] in inner:
            return
        node.set(attr, "{%s%s}" % (extra, (", " + inner) if inner else ""))
    elif not current:
        node.set(attr, "{%s}" % extra)


def _merge_domain(node):
    current = (node.get("domain") or "").strip()
    if "kanaan_is_counterparty" in current:
        return
    if current.startswith("[") and current.endswith("]") and current[1:-1].strip():
        node.set("domain", "[%s, %s]" % (PARTY_DOMAIN, current[1:-1].strip()))
    else:
        node.set("domain", "[%s]" % PARTY_DOMAIN)


def _top_level_fields(arch):
    """Field nodes of this model only (skip fields inside embedded x2many sub-views)."""
    for node in arch.iter("field"):
        if not any(a.tag == "field" for a in node.iterancestors()):
            yield node


class KanaanPartyFieldsMixin(models.AbstractModel):
    _name = "kanaan.party.fields.mixin"
    _description = "Kanaan: Party fields -> counterparties, timesheet add-line on top"

    def _kanaan_is_party_node(self, node, configured):
        fname = node.get("name")
        field = self._fields.get(fname)
        if not field or field.type not in ("many2one", "many2many") or field.comodel_name != "res.partner":
            return False
        if fname in NOT_PARTY:
            return False
        if fname in configured:
            return True
        if PARTY_LABEL.search(field.string or "") or PARTY_LABEL.search(node.get("string") or ""):
            return True
        return any(PARTY_PAGE.search(p.get("string") or "") for p in node.iterancestors("page"))

    @api.model
    def _get_view(self, view_id=None, view_type="form", **options):
        arch, view = super()._get_view(view_id, view_type, **options)
        if view_type not in ("form", "list"):
            return arch, view
        configured = set(get_party_fields(self.env, self._name))
        for node in _top_level_fields(arch):
            field = self._fields.get(node.get("name"))
            if not field:
                continue
            # 1. Party fields: only counterparties, new names become counterparties
            if self._kanaan_is_party_node(node, configured):
                _merge_domain(node)
                _merge_dict_attr(node, "context", PARTY_CTX_KEYS)
                _merge_dict_attr(node, "options", PARTY_OPTIONS)
            # 2. Timesheet tables (whatever view / Studio tab they're in): "Add a line" on top
            elif view_type == "form" and field.type == "one2many" and field.comodel_name == "account.analytic.line":
                node.set("widget", "one2many_add_top")
                for sub in node.iterchildren("list"):
                    sub.set("editable", "top")
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

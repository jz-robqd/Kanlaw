"""Studio field names are not in code, so they live in two system parameters.

On install they are auto-detected from the field labels and written to
Settings > Technical > System Parameters, where they can be corrected:

  kanaan_customizations.party_fields       e.g. "project.task:x_studio_party_1,project.task:x_studio_party_2"
  kanaan_customizations.file_number_field  e.g. "x_studio_file_number"   (field on project.task)

After editing a parameter, upgrade the module so cached views are rebuilt.
"""
import logging
import re

_logger = logging.getLogger(__name__)

PARAM_PARTY = "kanaan_customizations.party_fields"
PARAM_FILE_NO = "kanaan_customizations.file_number_field"

PARTY_LABEL = re.compile(r"party|counter.?part|opponent", re.I)
FILE_NO_LABEL = re.compile(r"file\s*(no|num|#)", re.I)


def _detect_party_fields(env):
    fields = env["ir.model.fields"].sudo().search([
        ("model", "in", ["project.task", "project.project"]),
        ("ttype", "=", "many2one"),
        ("relation", "=", "res.partner"),
        ("name", "=like", "x\\_%"),
    ])
    return [f"{f.model}:{f.name}" for f in fields if PARTY_LABEL.search(f.field_description or "")]


def _detect_file_number_field(env):
    fields = env["ir.model.fields"].sudo().search([
        ("model", "=", "project.task"),
        ("name", "=like", "x\\_%"),
        ("ttype", "in", ["char", "integer", "many2one", "text"]),
    ])
    match = fields.filtered(lambda f: FILE_NO_LABEL.search(f.field_description or ""))
    return match[:1].name or ""


def get_party_fields(env, model_name):
    raw = env["ir.config_parameter"].sudo().get_param(PARAM_PARTY, "")
    names = []
    for item in raw.split(","):
        model, _, fname = item.strip().partition(":")
        if model == model_name and fname in env[model_name]._fields:
            names.append(fname)
    return names


def get_file_number_field(env):
    fname = (env["ir.config_parameter"].sudo().get_param(PARAM_FILE_NO, "") or "").strip()
    return fname if fname in env["project.task"]._fields else False


def post_init_hook(env):
    icp = env["ir.config_parameter"].sudo()
    if not icp.get_param(PARAM_PARTY):
        party = _detect_party_fields(env)
        icp.set_param(PARAM_PARTY, ",".join(party))
        _logger.info("Kanaan: detected party fields %s", party)
    if not icp.get_param(PARAM_FILE_NO):
        file_no = _detect_file_number_field(env)
        icp.set_param(PARAM_FILE_NO, file_no)
        _logger.info("Kanaan: detected file number field %r", file_no)
    # Compute file number / case on existing documents now that the parameter is set.
    docs = env["documents.document"].sudo().search([("res_model", "=", "project.task")])
    docs._compute_kanaan_case()

from odoo import api, fields, models

LOOKUP_CTX = "kanaan_counterparty_lookup"


class ResPartner(models.Model):
    _inherit = "res.partner"

    kanaan_is_counterparty = fields.Boolean(
        string="Counterparty",
        index=True,
        copy=False,
        help="Opposing party. Hidden from non-admin users by a record rule; "
             "only reachable from the Party fields on matters.",
    )

    # The Party 1/2/3 fields pass `kanaan_counterparty_lookup` in their context.
    # Non-admins cannot read counterparties (record rule), so lookups from those
    # fields run as superuser: lawyers can pick an existing counterparty (or a
    # client, which flags a conflict) instead of creating duplicates.
    # Everywhere else (Contacts, client fields, emails) counterparties stay hidden.

    def _kanaan_lookup_env(self):
        return bool(self.env.context.get(LOOKUP_CTX)) and not self.env.su

    @api.model
    def web_name_search(self, name, specification, domain=None, operator="ilike", limit=100):
        if self._kanaan_lookup_env():
            return super(ResPartner, self.sudo()).web_name_search(
                name, specification, domain, operator, limit)
        return super().web_name_search(name, specification, domain, operator, limit)

    @api.model
    def web_search_read(self, domain, specification, offset=0, limit=None, order=None, count_limit=None):
        if self._kanaan_lookup_env():
            return super(ResPartner, self.sudo()).web_search_read(
                domain, specification, offset, limit, order, count_limit)
        return super().web_search_read(domain, specification, offset, limit, order, count_limit)

    @api.model
    def name_create(self, name):
        if self._kanaan_lookup_env():
            # new names typed in a Party field become counterparties
            return super(ResPartner, self.sudo().with_context(default_kanaan_is_counterparty=True)).name_create(name)
        return super().name_create(name)

    def action_kanaan_mark_counterparty(self):
        self.write({"kanaan_is_counterparty": True})

    def action_kanaan_unmark_counterparty(self):
        self.write({"kanaan_is_counterparty": False})

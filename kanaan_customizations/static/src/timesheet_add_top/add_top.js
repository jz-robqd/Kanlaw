import { registry } from "@web/core/registry";
import { ListRenderer } from "@web/views/list/list_renderer";
import { X2ManyField, x2ManyField } from "@web/views/fields/x2many/x2many_field";

export class AddTopListRenderer extends ListRenderer {
    static rowsTemplate = "kanaan_customizations.AddTopListRenderer.Rows";
}

export class AddTopX2ManyField extends X2ManyField {
    static components = { ...X2ManyField.components, ListRenderer: AddTopListRenderer };
}

registry.category("fields").add("one2many_add_top", {
    ...x2ManyField,
    component: AddTopX2ManyField,
});

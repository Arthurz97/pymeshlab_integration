import bpy


class MESHLAB_OT_reset_filter_settings(bpy.types.Operator):
    bl_idname = "meshlab.reset_filter_settings"
    bl_label = "Reset Filter Settings"
    bl_description = "Reset filter parameters to default values."
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        ui_state = context.scene.meshlab_ui_state
        active_filter = ui_state.filter_name
        props = getattr(context.scene, f"ml_{active_filter}", None)
        if props:
            for key in props.bl_rna.properties.keys():
                if key not in ["rna_type", "name"]:
                    props.property_unset(key)
        return {"FINISHED"}


class MESHLAB_PT_main_panel(bpy.types.Panel):
    bl_label = "PyMeshLab Integration"
    bl_idname = "MESHLAB_PT_main_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "PyMeshLab"

    def draw(self, context):
        layout = self.layout
        prefs = context.scene.meshlab_prefs
        addon_prefs = context.preferences.addons[__package__].preferences
        ui_state = context.scene.meshlab_ui_state

        layout.prop(ui_state, "category", text="Category")
        layout.prop(ui_state, "filter_name", text="Filter")

        active_filter = ui_state.filter_name
        if active_filter == "NONE":
            return

        props = getattr(context.scene, f"ml_{active_filter}", None)
        layout.separator()

        if props:
            layout.operator(
                "meshlab.reset_filter_settings", text="Reset Filter Settings"
            )
            # --- Ação sobre o objeto e Botão de Aplicar (Movidos para o topo) ---

            # Cria uma linha isolada usando o padrão 'split' nativo do Blender
            row_action = layout.row()
            row_action.use_property_split = True
            row_action.use_property_decorate = (
                False  # Oculta o ponto de keyframe de animação (opcional)
            )

            # Removemos o ':' do final do texto, pois o Blender no modo 'split' cuida da formatação sozinho.
            row_action.prop(prefs, "global_prev_mesh_action", text="Action on Selected")

            col = layout.column()
            col.scale_y = 1.5
            op = col.operator("meshlab.apply_filter", text="Apply Filter", icon="PLAY")
            op.filter_id = active_filter

            # Espaçamento para não grudar na caixa de parâmetros abaixo
            layout.separator()

            # --- Caixa de Parâmetros ---
            box_filter = layout.box()
            box_filter.label(text="Parameters:", icon="TOOL_SETTINGS")

            processed = set()

            for key in props.__class__.__annotations__.keys():
                if key in processed:
                    continue

                if key.endswith("_abs"):
                    base = key.replace("_abs", "")
                    perc_key = f"{base}_perc"
                    ui_label = props.bl_rna.properties[perc_key].name

                    diag = 1.0
                    obj = context.active_object
                    if obj and obj.type == "MESH":
                        diag = obj.dimensions.length
                        if diag == 0:
                            diag = 1.0

                    box_filter.label(text=f"{ui_label} (abs and %)")
                    row = box_filter.row(align=True)

                    col_abs = row.column()
                    col_abs.label(text="world unit")
                    col_abs.prop(props, key, text="")

                    col_perc = row.column()
                    col_perc.label(text=f"perc on(0 .. {diag:.4f})")
                    col_perc.prop(props, perc_key, text="")

                    processed.add(key)
                    processed.add(perc_key)

                elif not key.endswith("_perc"):
                    ui_label = props.bl_rna.properties[key].name
                    row = box_filter.row()
                    row.prop(props, key, text=ui_label)
                    processed.add(key)

import bpy  # type: ignore
from bpy.types import Panel  # type: ignore
from . import utils


class MESHLAB_PT_main_panel(Panel):
    bl_label = "MeshLab Integration"
    bl_idname = "MESHLAB_PT_main_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "MeshLab"

    def draw(self, context):
        layout = self.layout
        props = context.scene.meshlab_props
        dynamic_props = context.scene.meshlab_dynamic_props

        cat = props.category
        filt = props.filter_name

        filter_config = {}
        if filt and filt != "NONE" and cat in utils.CATEGORIES and filt in utils.CATEGORIES[cat]:
            filter_config = utils.CATEGORIES[cat][filt]

        filter_params_dict = filter_config.get("params", {})

        # --- 1. SELETORES DE CATEGORIA E FILTRO ---
        layout.prop(props, "category", text="Category")
        layout.prop(props, "filter_name", text="Filter")
        layout.separator()

        # Só exibe os controles se houver um filtro válido
        if filt and filt != "NONE" and filter_config:
            
            # --- 2. RESET FILTER SETTINGS (Fora da caixa preta, acima dos parâmetros) ---
            layout.operator("meshlab.reset_filter_settings", text="Reset Filter Settings")
            
            # --- 3. CAIXA DE PARÂMETROS DO FILTRO ---
            box_filter = layout.box()
            box_filter.label(text="Parameters:", icon="TOOL_SETTINGS")

            has_params = False

            # Desenha os parâmetros dinâmicos puros
            for p_name, p_info in filter_params_dict.items():
                unique_p_name = f"{filt}_{p_name}"
                if hasattr(dynamic_props, unique_p_name):
                    has_params = True
                    ui_label = p_info.get("name", p_name)
                    
                    row = box_filter.row()
                    if p_info.get("type") == "enum":
                        row.prop(dynamic_props, unique_p_name, text=ui_label, expand=True)
                    else:
                        row.prop(dynamic_props, unique_p_name, text=ui_label)

            if not has_params:
                box_filter.label(text="No parameters for this filter.")

            # --- 4. BOTÃO APPLY (Abaixo da caixa de parâmetros) ---
            layout.separator()
            col = layout.column()
            col.scale_y = 1.2
            col.operator("meshlab.apply_filter", text="Apply Filter", icon="PLAY")
            layout.separator()

        # --- 5. MENU DE EXPANSÃO (OBJECT SETTINGS) ---
        row = layout.row()
        icon = "TRIA_DOWN" if props.show_object_settings else "TRIA_RIGHT"
        row.prop(props, "show_object_settings", text="Object Settings", icon=icon, emboss=False)

        # Só mostra os botões se o menu estiver expandido
        if props.show_object_settings:
            # --- 6. RESET OBJECT SETTINGS (Abaixo do texto de expansão, acima do transfer, FORA da caixa) ---
            layout.operator("meshlab.reset_object_settings", text="Reset Object Settings")
            
            # --- 7. CAIXA PRETA DOS CONTROLES DO OBJETO ---
            box_obj = layout.box()
            box_obj.prop(props, "transfer_method", text="Transfer")
            
            # Texto descritivo padrão do Blender para clareza
            box_obj.separator()
            box_obj.label(text="Action on Selected:") 
            
            col_action = box_obj.column(align=True)
            col_action.prop(props, "global_prev_mesh_action", expand=True)
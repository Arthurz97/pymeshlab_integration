import bpy
from bpy.types import Panel
from . import utils

class MESHLAB_PT_main_panel(Panel):
    bl_label = "MeshLab Integration"
    bl_idname = "MESHLAB_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "MeshLab"
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.meshlab_props
        dynamic_props = context.scene.meshlab_dynamic_props
        
        layout.prop(props, "category", text="Category")
        layout.prop(props, "filter_name", text="Filter")
        
        cat = props.category
        filt = props.filter_name
        
        if filt and filt != "NONE" and cat in utils.CATEGORIES and filt in utils.CATEGORIES[cat]:
            filter_config = utils.CATEGORIES[cat][filt]
            filter_params_dict = filter_config.get('params', {})
            
            # Separamos quais são os parâmetros que vão para a nova caixa
            special_props = ["prev_mesh_action", "shade_smooth"]
            
            # --- 1. CAIXA DE PARÂMETROS GERAIS ---
            has_normal_params = any(p not in special_props for p in filter_params_dict.keys())
            if has_normal_params:
                box = layout.box()
                box.label(text="Parameters:", icon='TOOL_SETTINGS')
                
                for p_name, p_info in filter_params_dict.items():
                    if p_name in special_props:
                        continue # Pula os especiais para desenhar depois
                        
                    unique_p_name = f"{filt}_{p_name}"
                    if hasattr(dynamic_props, unique_p_name):
                        ui_label = p_info.get('name', p_name)
                        if p_info.get('type') == 'enum':
                            box.prop(dynamic_props, unique_p_name, text=ui_label, expand=True)
                        else:
                            box.prop(dynamic_props, unique_p_name, text=ui_label)
            
            # --- 2. BOTÃO APPLY FILTER (SUBIU PARA CÁ) ---
            layout.separator()
            col = layout.column()
            col.scale_y = 1.2
            col.operator("meshlab.apply_filter", text="Apply Filter", icon='PLAY')
            layout.separator()
            
            # --- 3. NOVA CAIXA "OBJECT PARAMETERS" ---
            has_special_params = any(p in special_props for p in filter_params_dict.keys())
            if has_special_params:
                obj_box = layout.box()
                obj_box.label(text="Object Parameters:", icon='OBJECT_DATA') # Ícone de Objeto adicionado
                
                for p_name in special_props:
                    if p_name in filter_params_dict:
                        p_info = filter_params_dict[p_name]
                        unique_p_name = f"{filt}_{p_name}"
                        
                        if hasattr(dynamic_props, unique_p_name):
                            ui_label = p_info.get('name', p_name)
                            if p_info.get('type') == 'enum':
                                obj_box.prop(dynamic_props, unique_p_name, text=ui_label, expand=True)
                            else:
                                obj_box.prop(dynamic_props, unique_p_name, text=ui_label)
            
            layout.separator()
            
            # (Mantido caso você use a chave antiga 'hide_original' em outros filtros)
            if filter_config.get('requires_selection', True) or filter_config.get('allow_hide', False):
                layout.prop(props, "hide_original")
                
            # --- 4. RESET SETTINGS NO FINAL ---
            layout.operator("meshlab.reset_settings")
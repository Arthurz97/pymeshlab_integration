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
            if filter_params_dict:
                box = layout.box()
                box.label(text="Parameters:", icon='TOOL_SETTINGS')
                
                # --- AQUI ESTA O CODIGO NOVO ---
                for p_name, p_info in filter_params_dict.items():
                    unique_p_name = f"{filt}_{p_name}"
                    
                    if hasattr(dynamic_props, unique_p_name):
                        # Puxamos o 'name' do JSON para forçar o rótulo correto na UI
                        ui_label = p_info.get('name', p_name)
                        
                        if p_info.get('type') == 'enum':
                            # expand=True transforma o Enum num grupo de botões horizontais
                            box.prop(dynamic_props, unique_p_name, text=ui_label, expand=True)
                        else:
                            box.prop(dynamic_props, unique_p_name, text=ui_label)
                # -------------------------------
            
            layout.separator()
            
            if filter_config.get('requires_selection', True):
                layout.prop(props, "hide_original")
                
            layout.operator("meshlab.reset_settings")
        
        layout.separator()
        
        col = layout.column()
        col.scale_y = 1.2
        col.operator("meshlab.apply_filter", text="Apply Filter", icon='PLAY')
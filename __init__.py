# Bloco essencial para recarregar todos os módulos quando você aperta F3 no Blender
if "bpy" in locals():
    import importlib
    importlib.reload(utils)
    importlib.reload(properties)
    importlib.reload(operators)
    importlib.reload(ui)
else:
    import bpy
    from bpy.props import PointerProperty
    from bpy.app.handlers import persistent
    from . import utils
    from . import properties
    from . import operators
    from . import ui

DynamicPropertyGroup = None
classes_to_register = []

@persistent
def addon_loaded_handler(dummy):
    if addon_loaded_handler in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(addon_loaded_handler)
    if bpy.context.scene.meshlab_props.category:
        utils.set_filter_defaults(bpy.context)

def register():
    global classes_to_register, DynamicPropertyGroup
    
    # Carrega os JSONs
    utils.load_filter_definitions()
    
    # Cria as propriedades dinâmicas
    DynamicPropertyGroup = properties.create_dynamic_properties_class()
    
    # Lista de registro
    classes_to_register = [
        properties.MESHLAB_props_filters,
        operators.MESHLAB_OT_reset_settings,
        operators.MESHLAB_OT_apply_filter,
        ui.MESHLAB_PT_main_panel
    ]
    
    bpy.utils.register_class(DynamicPropertyGroup)
    for cls in classes_to_register:
        bpy.utils.register_class(cls)
        
    bpy.types.Scene.meshlab_props = PointerProperty(type=properties.MESHLAB_props_filters)
    bpy.types.Scene.meshlab_dynamic_props = PointerProperty(type=DynamicPropertyGroup)
    bpy.app.handlers.load_post.append(addon_loaded_handler)

def unregister():
    global DynamicPropertyGroup
    
    if addon_loaded_handler in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(addon_loaded_handler)
        
    if hasattr(bpy.types.Scene, 'meshlab_dynamic_props'):
        del bpy.types.Scene.meshlab_dynamic_props
    if hasattr(bpy.types.Scene, 'meshlab_props'):
        del bpy.types.Scene.meshlab_props
        
    for cls in reversed(classes_to_register):
        if hasattr(bpy.utils, 'unregister_class'):
            bpy.utils.unregister_class(cls)
            
    if DynamicPropertyGroup:
        if hasattr(bpy.utils, 'unregister_class'):
            bpy.utils.unregister_class(DynamicPropertyGroup)
        DynamicPropertyGroup = None

if __name__ == "__main__":
    register()
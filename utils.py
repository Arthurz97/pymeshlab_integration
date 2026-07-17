import bpy, os, json

# Dicionário global para armazenar todos os filtros carregados
CATEGORIES = {}

def load_filter_definitions():
    CATEGORIES.clear()
    addon_dir = os.path.dirname(__file__)
    categories_dir = os.path.join(addon_dir, "categories")
    
    if not os.path.exists(categories_dir):
        return
        
    for filename in sorted(os.listdir(categories_dir)):
        if filename.endswith(".json"):
            category_name = os.path.splitext(filename)[0]
            with open(os.path.join(categories_dir, filename), 'r', encoding='utf-8') as f:
                CATEGORIES[category_name] = json.load(f)

def set_filter_defaults(context):
    props = context.scene.meshlab_props
    dynamic_props = context.scene.meshlab_dynamic_props
    cat = props.category
    filt = props.filter_name
    
    if filt and filt != "NONE" and cat in CATEGORIES and filt in CATEGORIES[cat]:
        for p_name, p_info in CATEGORIES[cat][filt].get('params', {}).items():
            unique_p_name = f"{filt}_{p_name}"
            
            if hasattr(dynamic_props, unique_p_name):
                default_val = p_info.get('default')
                if default_val is not None:
                    try:
                        setattr(dynamic_props, unique_p_name, default_val)
                    except TypeError:
                        pass
                        
    if getattr(context, 'area', None):
        for region in context.area.regions:
            if region.type == 'UI':
                region.tag_redraw()
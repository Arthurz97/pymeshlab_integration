import bpy
import uuid
from bpy.types import PropertyGroup
from bpy.props import EnumProperty, BoolProperty, FloatProperty, IntProperty, StringProperty
from . import utils

def update_ui_and_defaults(self, context):
    utils.set_filter_defaults(context)

class MESHLAB_props_filters(PropertyGroup):
    def get_categories(self, context):
        keys = sorted(utils.CATEGORIES.keys())
        if not keys:
            return [("NONE", "None", "")]
        
        items = []
        for k in keys:
            desc = utils.CATEGORIES[k].get("__category_info__", {}).get("description", f"{k.replace('_', ' ')} filters")
            items.append((k, k.replace('_', ' '), desc))
        return items

    def get_filters(self, context):
        cat = self.category
        if cat in utils.CATEGORIES:
            filters = sorted([f for f in utils.CATEGORIES[cat].keys() if not f.startswith("__")])
            if filters:
                items = []
                for f in filters:
                    ui_name = utils.CATEGORIES[cat][f].get("ui_name", f.replace('_', ' ').title())
                    desc = utils.CATEGORIES[cat][f].get("description", "")
                    items.append((f, ui_name, desc))
                return items
        return [("NONE", "No filter", "")]
            
    category: EnumProperty(name="Category", items=get_categories, update=update_ui_and_defaults)
    filter_name: EnumProperty(name="Filter", items=get_filters, update=update_ui_and_defaults)
    
    hide_original: BoolProperty(
        name="Hide Original", 
        description="Hide the original object after processing", 
        default=True
    )

def create_dynamic_properties_class():
    all_params = {}
    props = {}
    
    for cat, filters in utils.CATEGORIES.items():
        for filt, data in filters.items():
            if filt.startswith("__"):
                continue
            for p_name, p_info in data.get('params', {}).items():
                # CRIAMOS UM NOME UNICO PARA A PROPRIEDADE
                unique_p_name = f"{filt}_{p_name}"
                if unique_p_name not in all_params:
                    all_params[unique_p_name] = p_info
                    
    for p_name, p_info in all_params.items():
        p_type = p_info.get('type')
        
        kwargs = {
            'name': p_info.get('name', p_name.replace('_', ' ').title()),
            'description': p_info.get('description', '')
        }
        if 'min' in p_info: kwargs['min'] = int(p_info['min']) if p_type == 'int' else float(p_info['min'])
        if 'max' in p_info: kwargs['max'] = int(p_info['max']) if p_type == 'int' else float(p_info['max'])
        if 'soft_min' in p_info: kwargs['soft_min'] = int(p_info['soft_min']) if p_type == 'int' else float(p_info['soft_min'])
        if 'soft_max' in p_info: kwargs['soft_max'] = int(p_info['soft_max']) if p_type == 'int' else float(p_info['soft_max'])
        if 'default' in p_info: kwargs['default'] = p_info['default']
        
        if p_type == 'float':
            if 'min' not in kwargs: kwargs['min'] = -3.4e+38
            if 'max' not in kwargs: kwargs['max'] = 3.4e+38
            
            # Repassando a configuração baseada nos addons nativos e mmgpy
            if 'subtype' in p_info: kwargs['subtype'] = p_info['subtype']
            if 'unit' in p_info: kwargs['unit'] = p_info['unit']
            if 'step' in p_info: kwargs['step'] = int(p_info['step'])
            if 'precision' in p_info: kwargs['precision'] = int(p_info['precision'])
            
            props[p_name] = FloatProperty(**kwargs)
            
        elif p_type == 'int':
            if 'min' not in kwargs: kwargs['min'] = -2147483648
            if 'max' not in kwargs: kwargs['max'] = 2147483647
            
            if 'subtype' in p_info: kwargs['subtype'] = p_info['subtype']
            if 'step' in p_info: kwargs['step'] = int(p_info['step'])
            
            props[p_name] = IntProperty(**kwargs)
            
        elif p_type == 'bool':
            props[p_name] = BoolProperty(**kwargs)
            
        elif p_type in ['string', 'PercentageValue', 'AbsoluteValue']:
            props[p_name] = StringProperty(**kwargs)
            
        elif p_type == 'enum':
            p_items = p_info.get('items', [])
            valid_items = [tuple(item) for item in p_items if isinstance(item, list) and len(item) == 3]
            if valid_items:
                kwargs['items'] = valid_items
                props[p_name] = EnumProperty(**kwargs)
                
    # GERA UM NOME ÚNICO: Força o Blender a esquecer a UI antiga e recriar a propriedade do zero.
    class_name = f"MESHLAB_dynamic_props_{uuid.uuid4().hex[:8]}"
    return type(class_name, (PropertyGroup,), {"__annotations__": props})
import bpy
from bpy.props import EnumProperty

UI_MAPPING = {
    "MESHLAB_CLASSIC": {
        "Create New Mesh": [
            "create_cube",
            "create_sphere",
            "create_sphere_cap",
            "create_torus",
            "create_annulus",
            "create_cone",
        ],
        "Remeshing, Simplification and Reconstruction": [
            "meshing_isotropic_explicit_remeshing"
        ],
    },
    "BLENDER_CUSTOM": {
        "Basic Shapes": ["create_cube", "create_sphere"],
        "Advanced Remesh": ["meshing_isotropic_explicit_remeshing"],
    },
}

FILTER_NAMES = {
    "create_cube": "Box/Cube",
    "create_sphere": "Sphere",
    "create_sphere_cap": "Sphere Cap",
    "create_torus": "Torus",
    "create_annulus": "Annulus",
    "create_cone": "Cone",
    "meshing_isotropic_explicit_remeshing": "Remeshing: Isotropic Explicit Remeshing",
}

FILTER_DESCRIPTIONS = {
    "create_cube": "Create a Box, Cube, Hexahedron. You can specify the side length.",
    "create_sphere": "Create a Sphere, whose topology is obtained as regular subdivision of an icosahedron.",
    "create_sphere_cap": "Create a Sphere Cap, or spherical dome, subtended by a cone of given angle.",
    "create_torus": "Create a Torus",
    "create_annulus": "Create an Annulus e.g. a flat region bounded by two concentric circles, or a holed disk.",
    "create_cone": "Create a Cone",
    "meshing_isotropic_explicit_remeshing": "Perform a explicit remeshing of a triangular mesh, by repeatedly applying edge flip, collapse, relax and refine operations.",
}

# --- NOVO DICIONÁRIO: DESCRIÇÕES DAS CATEGORIAS ---
CATEGORY_DESCRIPTIONS = {
    "Create New Mesh": "Tools and filters for generating new 3D meshes and primitives from scratch.",
    "Remeshing, Simplification and Reconstruction": "Filters for remeshing, simplifying, and reconstructing 3D models.",
}


class MESHLAB_preferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    layout_mode: EnumProperty(
        name="Layout Mode",
        description="Choose the UI structure.",
        items=[
            ("MESHLAB_CLASSIC", "MeshLab Classic", "Standard MeshLab structure"),
            ("BLENDER_CUSTOM", "Blender Custom", "Simplified for 3D artists"),
        ],
        default="MESHLAB_CLASSIC",
    )

    units_mode: EnumProperty(
        name="Parameter Units",
        description="Choose how mathematical values are displayed.",
        items=[
            ("RAW_MATH", "Raw Math", "Show raw percentage values"),
            ("BLENDER_UNITS", "Blender Units", "Show synchronized absolute dimensions"),
        ],
        default="RAW_MATH",
    )

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.label(text="Global Configuration", icon="PREFERENCES")
        box.prop(self, "layout_mode")
        box.prop(self, "units_mode")


class MESHLAB_props_preferences(bpy.types.PropertyGroup):
    global_prev_mesh_action: EnumProperty(
        name="Action on Selected",
        description="Choose what to do with the originally selected object.",
        # A tupla completa exige 5 elementos no Blender moderno: (ID, Nome, Descrição, Ícone, Valor Inteiro)
        items=[
            (
                "KEEP",
                "Keep",
                "Keeps the selected object untouched.",
                "OUTLINER_OB_MESH",
                0,
            ),
            ("HIDE", "Hide", "Hides the selected object.", "HIDE_ON", 1),
            (
                "DELETE",
                "Delete",
                "Permanently deletes the selected object.",
                "TRASH",
                2,
            ),
        ],
        default="HIDE",
    )


def update_category(self, context):
    prefs = context.preferences.addons[__package__].preferences
    mapping = UI_MAPPING.get(prefs.layout_mode, {})
    cat = self.category
    if cat in mapping:
        # Ordena usando o Nome Visual antes de selecionar o primeiro automaticamente
        valid_filters = sorted(
            mapping[cat], key=lambda f: FILTER_NAMES.get(f, f.replace("_", " ").title())
        )
        if valid_filters and self.filter_name not in valid_filters:
            self.filter_name = valid_filters[0]


def get_categories(self, context):
    prefs = context.preferences.addons[__package__].preferences
    mapping = UI_MAPPING.get(prefs.layout_mode, {})
    return [(k, k, CATEGORY_DESCRIPTIONS.get(k, "")) for k in sorted(mapping.keys())]


def get_filters(self, context):
    prefs = context.preferences.addons[__package__].preferences
    mapping = UI_MAPPING.get(prefs.layout_mode, {})
    cat = context.scene.meshlab_ui_state.category

    if cat not in mapping:
        return [("NONE", "No filter", "")]

    # Gera os itens e ordena especificamente pelo índice [1] (o Nome Visual da UI)
    filters = mapping[cat]
    items = [
        (
            f,
            FILTER_NAMES.get(f, f.replace("_", " ").title()),
            FILTER_DESCRIPTIONS.get(f, ""),
        )
        for f in filters
    ]
    items.sort(key=lambda x: x[1])

    return items if items else [("NONE", "No filter", "")]


class MESHLAB_props_ui_state(bpy.types.PropertyGroup):
    category: EnumProperty(
        name="Category", items=get_categories, update=update_category
    )
    filter_name: EnumProperty(name="Filter", items=get_filters)

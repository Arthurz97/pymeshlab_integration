import bpy
from bpy.props import EnumProperty

UI_MAPPING = {
    "Create New Mesh": [
        "create_cube",
        "create_sphere",
        "create_sphere_cap",
        "create_torus",
        "create_annulus",
        "create_cone",
    ],
    "Remeshing, Simplification and Reconstruction": [
        "meshing_isotropic_explicit_remeshing",
        "generate_resampled_uniform_mesh",
    ],
}

FILTER_NAMES = {
    "create_cube": "Box/Cube",
    "create_sphere": "Sphere",
    "create_sphere_cap": "Sphere Cap",
    "create_torus": "Torus",
    "create_annulus": "Annulus",
    "create_cone": "Cone",
    "meshing_isotropic_explicit_remeshing": "Remeshing: Isotropic Explicit Remeshing",
    "generate_resampled_uniform_mesh": "Uniform Mesh Resampling",
}

FILTER_DESCRIPTIONS = {
    "create_cube": "Create a Box, Cube, Hexahedron. You can specify the side length.",
    "create_sphere": "Create a Sphere, whose topology is obtained as regular subdivision of an icosahedron.",
    "create_sphere_cap": "Create a Sphere Cap, or spherical dome, subtended by a cone of given angle.",
    "create_torus": "Create a Torus",
    "create_annulus": "Create an Annulus e.g. a flat region bounded by two concentric circles, or a holed disk.",
    "create_cone": "Create a Cone",
    "meshing_isotropic_explicit_remeshing": "Perform a explicit remeshing of a triangular mesh, by repeatedly applying edge flip, collapse, relax and refine operations.",
    "generate_resampled_uniform_mesh": "Create a new mesh that is a resampled version of the current one. The resampling is done by building a uniform volumetric representation where each voxel contains the signed distance from the original surface. The resampled surface is reconstructed using the marching cube algorithm over this volume.",
}


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


# Captura o primeiro filtro da primeira categoria para ser o default
_default_filter = "NONE"
if UI_MAPPING:
    _first_category_filters = list(UI_MAPPING.values())[0]
    if _first_category_filters:
        # Ordena usando a mesma lógica visual para garantir que o primeiro seja o correto
        _sorted_filters = sorted(
            _first_category_filters,
            key=lambda f: FILTER_NAMES.get(f, f.replace("_", " ").title()),
        )
        _default_filter = _sorted_filters[0] if _sorted_filters else "NONE"


class MESHLAB_props_ui_state(bpy.types.PropertyGroup):
    filter_name: bpy.props.StringProperty(name="Filter", default=_default_filter)

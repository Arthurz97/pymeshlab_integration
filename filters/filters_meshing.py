import bpy
from bpy.types import PropertyGroup
from bpy.props import FloatProperty, IntProperty, BoolProperty
from ..base_filter import MeshLabFilterBase

# ==============================================================================
# Arquivo criado baseado no nome das classes da api do PyMeshLab.
# Filtros que exigem seleção de malhas e cálculos de bounding box.
# ==============================================================================

# --- FUNÇÕES MATEMÁTICAS CONTÍNUAS ---
# Gerenciam as propriedades '_abs' e '_perc' para simular o PercentageValue do PyMeshLab.
# A conversão ocorre em tempo real usando a diagonal / Bounding Box do objeto ativo.


def get_abs_val(self, prop_name):
    obj = bpy.context.active_object
    diag = obj.dimensions.length if (obj and obj.type == "MESH") else 1.0
    diag = diag if diag > 0 else 1.0
    val_perc = getattr(self, prop_name)
    return (val_perc / 100.0) * diag


def set_abs_val(self_obj, value, prop_name):
    obj = bpy.context.active_object
    diag = obj.dimensions.length if (obj and obj.type == "MESH") else 1.0
    diag = diag if diag > 0 else 1.0
    val_abs = max(0.0, min(value, diag))
    setattr(self_obj, prop_name, (val_abs / diag) * 100.0)


class MESHLAB_PG_meshing_isotropic_explicit_remeshing(PropertyGroup, MeshLabFilterBase):
    pymeshlab_filter = "meshing_isotropic_explicit_remeshing"
    requires_selection = True
    shade_flat = True
    remove_attributes = ["quality", "texture_u", "texture_v", "sharp_face", "Col"]

    iterations: IntProperty(
        name="Iterations",
        description="Number of iterations of the remeshing operations to repeat on the mesh.",
        default=10,
        min=0,
    )
    adaptive: BoolProperty(
        name="Adaptive remeshing",
        description="Toggles adaptive isotropic remeshing.",
        default=False,
    )
    selectedonly: BoolProperty(
        name="Remesh only selected faces",
        description="If checked the remeshing operations will be applied only to the selected faces.",
        default=False,
    )

    # Precisão Matemática Fixada em 3 decimais de 50 steps (perc) e 6 decimais de 1 step (abs)
    targetlen_perc: FloatProperty(
        name="Target Length",
        description="Sets the target length for the remeshed mesh edges.",
        default=1.0,
        min=0.0,
        max=100.0,
        precision=3,
        step=50,
    )
    targetlen_abs: FloatProperty(
        name="world unit",
        description="Sets the target length for the remeshed mesh edges.",
        get=lambda s: get_abs_val(s, "targetlen_perc"),
        set=lambda s, v: set_abs_val(s, v, "targetlen_perc"),
        precision=6,
        step=1,
    )

    featuredeg: FloatProperty(
        name="Crease Angle",
        description="Minimum angle between faces of the original to consider the shared edge as a feature to be preserved.",
        default=30.0,
        min=0.0,
        max=180.0,
    )
    checksurfdist: BoolProperty(
        name="Check Surface Distance",
        description="If toggled each local operation must deviate from original mesh by [Max. surface distance].",
        default=False,
    )

    maxsurfdist_perc: FloatProperty(
        name="Max. Surface Distance",
        description="Maximal surface deviation allowed for each local operation.",
        default=1.0,
        min=0.0,
        max=100.0,
        precision=3,
        step=50,
    )
    maxsurfdist_abs: FloatProperty(
        name="world unit",
        description="Maximal surface deviation allowed for each local operation.",
        get=lambda s: get_abs_val(s, "maxsurfdist_perc"),
        set=lambda s, v: set_abs_val(s, v, "maxsurfdist_perc"),
        precision=6,
        step=1,
    )

    splitflag: BoolProperty(
        name="Refine Step",
        description="If checked the remeshing operations will include a refine step.",
        default=True,
    )
    collapseflag: BoolProperty(
        name="Collapse Step",
        description="If checked the remeshing operations will include a collapse step.",
        default=True,
    )
    swapflag: BoolProperty(
        name="Edge-Swap Step",
        description="If checked the remeshing operations will include a edge-swap step, aimed at improving the vertex valence of the resulting mesh.",
        default=True,
    )
    smoothflag: BoolProperty(
        name="Smooth Step",
        description="If checked the remeshing operations will include a smoothing step, aimed at relaxing the vertex positions in a Laplacian sense.",
        default=True,
    )
    reprojectflag: BoolProperty(
        name="Reproject Step",
        description="If checked the remeshing operations will include a step to reproject the mesh vertices on the original surface.",
        default=True,
    )

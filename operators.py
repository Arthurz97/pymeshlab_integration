import bpy, os, tempfile, math
from bpy.types import Operator
from mathutils import Matrix
import pymeshlab
from . import utils


class MESHLAB_OT_reset_filter_settings(Operator):
    bl_idname = "meshlab.reset_filter_settings"
    bl_label = "Reset Filter Settings"
    bl_description = "Reset filter parameters to default values."
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        props = context.scene.meshlab_props
        return props.category != "NONE" and props.filter_name != "NONE"

    def execute(self, context):
        utils.set_filter_defaults(context)
        return {"FINISHED"}


class MESHLAB_OT_reset_object_settings(Operator):
    bl_idname = "meshlab.reset_object_settings"
    bl_label = "Reset Object Settings"
    bl_description = "Reset global object parameters."
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        props = context.scene.meshlab_props
        props.global_prev_mesh_action = "HIDE"
        props.transfer_method = "DISK"
        return {"FINISHED"}


class MESHLAB_OT_apply_filter(Operator):
    bl_idname = "meshlab.apply_filter"
    bl_label = "Apply MeshLab Filter"
    bl_description = "Apply the selected filter using PyMeshLab."
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.area and context.area.type == "VIEW_3D"

    def execute(self, context):
        # Trava de segurança: Garante que estamos no Object Mode para não dar erro
        if context.active_object and context.active_object.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")

        props = context.scene.meshlab_props
        dynamic_props = context.scene.meshlab_dynamic_props
        cat = props.category
        filt = props.filter_name

        if filt == "NONE" or not filt:
            self.report({"WARNING"}, "No filter selected.")
            return {"CANCELLED"}

        filter_config = utils.CATEGORIES[cat][filt]
        requires_selection = filter_config.get("requires_selection", True)

        original_obj = context.active_object
        has_mesh = original_obj and original_obj.type == "MESH"
        original_selected_objs = context.selected_objects[:]

        # TRAVA DE MULTI-SELEÇÃO: Permite apenas 1 seleção de objeto no máximo
        if len(original_selected_objs) > 1:
            self.report(
                {"ERROR"},
                "Múltiplas seleções não são suportadas. Selecione apenas 1 objeto.",
            )
            return {"CANCELLED"}

        if requires_selection and (not original_selected_objs or not has_mesh):
            self.report(
                {"ERROR"}, "This filter requires exactly one active mesh selection."
            )
            return {"CANCELLED"}

        transfer_method = props.transfer_method
        apply_prev_mesh_action = props.global_prev_mesh_action

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                output_path = os.path.join(tmpdir, "output.obj")
                ms = pymeshlab.MeshSet()

                if transfer_method == "MEMORY":
                    self.report(
                        {"INFO"},
                        "Memory transfer (NumPy) in development. Using Disk as fallback.",
                    )

                if requires_selection and has_mesh:
                    input_path = os.path.join(tmpdir, "input.obj")
                    bpy.ops.object.select_all(action="DESELECT")
                    original_obj.select_set(True)
                    bpy.ops.wm.obj_export(
                        filepath=input_path,
                        export_selected_objects=True,
                        export_materials=False,
                        global_scale=1.0,
                    )
                    ms.load_new_mesh(input_path)

                params = {}
                filter_params_dict = filter_config.get("params", {})

                for p_name, p_info in filter_params_dict.items():
                    unique_p_name = f"{filt}_{p_name}"

                    if hasattr(dynamic_props, unique_p_name):
                        value = getattr(dynamic_props, unique_p_name)
                        p_type = p_info.get("type")

                        if p_type == "PercentageValue":
                            try:
                                params[p_name] = pymeshlab.PercentageValue(
                                    float(str(value).strip().replace("%", ""))
                                )
                            except:
                                params[p_name] = value
                        elif p_type == "AbsoluteValue":
                            try:
                                params[p_name] = pymeshlab.AbsoluteValue(float(value))
                            except:
                                params[p_name] = value
                        else:
                            params[p_name] = value

                ms.apply_filter(filt, **params)
                ms.save_current_mesh(output_path)

                bpy.ops.wm.obj_import(filepath=output_path)

                if context.selected_objects:
                    new_obj = context.selected_objects[0]
                else:
                    self.report({"ERROR"}, "Failed to import the processed mesh.")
                    return {"CANCELLED"}

                # Sempre aplica a correção do eixo X exigida pelo importador OBJ do Blender
                correction_matrix = Matrix.Rotation(math.radians(90), 4, "X")
                new_obj.data.transform(correction_matrix)

                if requires_selection and has_mesh:
                    # 1. Desfaz a transformação global nos vértices
                    new_obj.data.transform(original_obj.matrix_world.inverted())

                    # 2. Copia exatamente o Location, Rotation e Scale do original
                    new_obj.matrix_world = original_obj.matrix_world.copy()

                    # 3. Tratamento de nome: extrai o nome base e adiciona o sufixo.
                    # O Blender cuidará automaticamente das numerações .001, .002, etc.
                    base_name = original_obj.name.split("_pymeshlab")[0]
                    new_obj.name = f"{base_name}_pymeshlab"

                else:
                    # Criando novo nome com o sufixo em minúsculo para filtros de criação
                    obj_name = filter_config["object_name"]
                    new_obj.name = f"{obj_name}_pymeshlab"
                    new_obj.location = context.scene.cursor.location
                    new_obj.rotation_euler = (0, 0, 0)
                    new_obj.scale = (1, 1, 1)

                # Atualiza a geometria no Blender para refletir os cálculos
                new_obj.data.update()

                bpy.ops.object.select_all(action="DESELECT")
                new_obj.select_set(True)
                context.view_layer.objects.active = new_obj

                if new_obj.type == "MESH" and new_obj.data:
                    attrs_to_remove = filter_config.get("remove_attributes", [])
                    for attr in attrs_to_remove:
                        if attr in new_obj.data.attributes:
                            new_obj.data.attributes.remove(
                                new_obj.data.attributes[attr]
                            )

                if filter_config.get("shade_flat", False):
                    bpy.ops.object.shade_flat()

                # Action on Selected: Removemos o teste de prefixo e aplicamos indiscriminadamente ao objeto anterior selecionado
                if apply_prev_mesh_action in ["HIDE", "DELETE"]:
                    for obj in original_selected_objs:
                        if obj:
                            if apply_prev_mesh_action == "HIDE":
                                obj.hide_set(True)
                                obj.hide_render = True
                            elif apply_prev_mesh_action == "DELETE":
                                bpy.data.objects.remove(obj, do_unlink=True)

                self.report({"INFO"}, f"Filter '{filt}' applied successfully!")
            return {"FINISHED"}

        except Exception as e:
            self.report({"ERROR"}, f"Error applying filter: {str(e)}")
            return {"CANCELLED"}

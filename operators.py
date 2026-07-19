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
        # SEGURANÇA DE MODO: Garante que o Blender esteja no modo Objeto.
        # Evita crashes caso o usuário tente rodar o filtro de dentro do Edit Mode.
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

        # TRAVA DE MULTI-SELEÇÃO: O PyMeshLab em scripts simples pode se perder com múltiplos inputs.
        # Esta trava garante que a lógica de nomeação e matriz funcione perfeitamente sobre 1 único alvo.
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

        # ---- TRAVA DE SEGURANÇA (ANTES DA EXPORTAÇÃO) ----
        # Bloqueia a execução imediatamente se a caixa estiver marcada mas a seleção estiver vazia.
        unique_sel_name = f"{filt}_selectedonly"
        is_selected_only_checked = hasattr(dynamic_props, unique_sel_name) and getattr(
            dynamic_props, unique_sel_name
        )

        if is_selected_only_checked and original_obj and original_obj.type == "MESH":
            # Checa os polígonos. Como o Object Mode é forçado no início da função, p.select está sempre atualizado.
            has_selection = any(p.select for p in original_obj.data.polygons)
            if not has_selection:
                self.report(
                    {"WARNING"},
                    "Opção 'Remesh only selected faces' ativa, mas nenhuma face está selecionada. Cancele o script ou selecione faces no Edit Mode.",
                )
                return {"CANCELLED"}

        apply_prev_mesh_action = props.global_prev_mesh_action

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                output_path = os.path.join(tmpdir, "output.ply")
                ms = pymeshlab.MeshSet()

                # LEITURA PRÉVIA DO PARÂMETRO 'selectedonly'
                is_selected_only = False
                unique_sel_name = f"{filt}_selectedonly"
                if hasattr(dynamic_props, unique_sel_name):
                    is_selected_only = getattr(dynamic_props, unique_sel_name)

                # EXPORTAÇÃO (DISK): Salva a malha selecionada temporariamente para ser lida pelo PyMeshLab
                if requires_selection and has_mesh:
                    input_path = os.path.join(tmpdir, "input.ply")
                    bpy.ops.object.select_all(action="DESELECT")
                    original_obj.select_set(True)

                    # Sincroniza a memória do Blender
                    context.view_layer.update()
                    original_obj.data.update()

                    # ---- 1. PROTEÇÃO DE CORES E TRANSFERÊNCIA DE SELEÇÃO ----
                    temp_color = None
                    export_kwargs = {
                        "filepath": input_path,
                        "export_selected_objects": True,
                    }

                    if is_selected_only:
                        # USAMOS POINT (Vértices) porque o PLY C++ garante essa exportação
                        temp_color = original_obj.data.color_attributes.new(
                            name="Col", type="BYTE_COLOR", domain="POINT"
                        )
                        original_obj.data.attributes.active_color = temp_color

                        # Extrai a seleção diretamente dos vértices
                        colors = [
                            val
                            for v in original_obj.data.vertices
                            for val in (
                                (1.0, 1.0, 1.0, 1.0)
                                if v.select
                                else (0.0, 0.0, 0.0, 1.0)
                            )
                        ]
                        temp_color.data.foreach_set("color", colors)

                        export_kwargs["export_colors"] = "SRGB"

                    # Exporta dinamicamente passando os parâmetros seguros
                    bpy.ops.wm.ply_export(**export_kwargs)

                    # Limpeza imediata para manter seu objeto original intacto
                    if temp_color:
                        original_obj.data.color_attributes.remove(temp_color)

                    ms.load_new_mesh(input_path)

                    # ---- 2. TRADUÇÃO DA SELEÇÃO NO PYMESHLAB ----
                    if is_selected_only:
                        # Seleciona os vértices pintados de branco (r > 127)
                        ms.compute_selection_by_condition_per_vertex(
                            condselect="(r > 127)"
                        )
                        # Propaga a seleção dos vértices para as faces (Método Inclusivo Estável)
                        ms.compute_selection_transfer_vertex_to_face()

                # LEITURA DE PARÂMETROS DINÂMICOS DA UI
                params = {}
                filter_params_dict = filter_config.get("params", {})

                for p_name, p_info in filter_params_dict.items():
                    unique_p_name = f"{filt}_{p_name}"
                    p_type = p_info.get("type")

                    # Lógica especial para PercentageValue: no Blender separamos em '_abs' e '_perc'
                    # para melhorar a UI, mas para o PyMeshLab mandamos exclusivamente o valor percentual limpo.
                    if p_type == "PercentageValue":
                        perc_name = f"{unique_p_name}_perc"
                        if hasattr(dynamic_props, perc_name):
                            val = getattr(dynamic_props, perc_name)
                            params[p_name] = pymeshlab.PercentageValue(float(val))

                    elif hasattr(dynamic_props, unique_p_name):
                        value = getattr(dynamic_props, unique_p_name)

                        if p_type == "AbsoluteValue":
                            try:
                                params[p_name] = pymeshlab.AbsoluteValue(float(value))
                            except:
                                params[p_name] = value
                        else:
                            params[p_name] = value

                # EXECUÇÃO: Aplica o filtro com os parâmetros mapeados e salva no disco.
                ms.apply_filter(filt, **params)
                ms.save_current_mesh(output_path)

                # SEGURANÇA DE FALHA: Se o PyMeshLab falhar silenciosamente (ex: malha impossível de dar remesh),
                # bloqueia o erro do Blender de não encontrar o 'output.ply'.
                if not os.path.exists(output_path):
                    self.report(
                        {"ERROR"},
                        "PyMeshLab falhou ao gerar a malha. Verifique os parâmetros.",
                    )
                    return {"CANCELLED"}

                # IMPORTAÇÃO DA MALHA PROCESSADA
                bpy.ops.wm.ply_import(filepath=output_path)

                if context.selected_objects:
                    new_obj = context.selected_objects[0]
                else:
                    self.report({"ERROR"}, "Failed to import the processed mesh.")
                    return {"CANCELLED"}

                # A matriz de correção de 90 graus no eixo X foi removida daqui,
                # pois o importador PLY nativo mantém a orientação original correta.

                if requires_selection and has_mesh:
                    # RESTAURAÇÃO DE MATRIZ: Se o objeto original tinha escala ou rotação aplicadas em Object Mode,
                    # a exportação/importação bagunça isso. Esse bloco injeta a World Matrix exata do objeto original no novo.
                    new_obj.data.transform(original_obj.matrix_world.inverted())
                    new_obj.matrix_world = original_obj.matrix_world.copy()

                    # NOMEAÇÃO AUTOMÁTICA (Filtros de edição):
                    # O ".split" limpa sufixos antigos (evitando Cube_pymeshlab_pymeshlab).
                    # Ao injetar "_pymeshlab" no fim, o próprio Blender gerencia sufixos ".001", ".002" caso haja nomes duplicados na cena.
                    base_name = original_obj.name.split("_pymeshlab")[0]
                    new_obj.name = f"{base_name}_pymeshlab"

                else:
                    # NOMEAÇÃO AUTOMÁTICA (Filtros de criação como o Primitive Cube):
                    obj_name = filter_config.get("object_name", filt)
                    new_obj.name = f"{obj_name}_pymeshlab"
                    new_obj.location = context.scene.cursor.location
                    new_obj.rotation_euler = (0, 0, 0)
                    new_obj.scale = (1, 1, 1)

                new_obj.data.update()

                # CONFIGURAÇÃO DE ATIVIDADE: Define o recém-criado como ativo na cena.
                bpy.ops.object.select_all(action="DESELECT")
                new_obj.select_set(True)
                context.view_layer.objects.active = new_obj

                # LIMPEZA DE ATRIBUTOS: O PyMeshLab/PLY pode gerar sujeira como normais travadas ou UVs residuais.
                if new_obj.type == "MESH" and new_obj.data:
                    attrs_to_remove = filter_config.get("remove_attributes", [])
                    for attr in attrs_to_remove:
                        if attr in new_obj.data.attributes:
                            new_obj.data.attributes.remove(
                                new_obj.data.attributes[attr]
                            )

                # SHADE FLAT: Aplicável a primitivas criadas ou malhas onde normais suaves causem artefatos visuais.
                if filter_config.get("shade_flat", False):
                    bpy.ops.object.shade_flat()

                # AÇÃO SOBRE O OBJETO ANTERIOR (Keep, Hide, Delete)
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

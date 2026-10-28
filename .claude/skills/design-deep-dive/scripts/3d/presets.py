# Blender 5.2.2 / glTF-Blender-IO 5.2.40 — пресеты bpy.ops.export_scene.gltf для веба (three r186). [проверено]
# Импорт: exec(open(".../presets.py").read()) или sys.path + import presets; export(path, PRESET, **overrides)

BASE_WEB = dict(
    export_format="GLB",
    export_yup=True,                      # glTF Y-up (иначе модель «лежит»)
    export_apply=True,                    # модификаторы — уровень ВЬЮПОРТА (levels); у объектов С модификаторами теряются shape keys
    export_texcoords=True,
    export_normals=True,
    export_tangents=False,                # three строит касательные сам; True — если нужна точная карта нормалей
    export_materials="EXPORT",
    export_image_format="AUTO",           # исходные JPEG/PNG байт в байт; WebP/KTX2 — постобработкой
    export_vertex_color="MATERIAL",
    export_all_vertex_colors=False,       # иначе фиктивный COLOR_0 и баг 5.2.40 с несколькими атрибутами
    export_attributes=False,
    export_extras=True,                   # custom properties → userData для JS
    export_cameras=False,
    export_lights=False,                  # свет — кодом на странице (или COMPAT, см. 01 §7)
    use_renderable=True,                  # без объектов с hide_render
    use_visible=True,                     # без скрытых и исключённых коллекций
    export_animations=False,
    export_draco_mesh_compression_enable=False,
    export_meshopt_compression_enable=False,   # сжатие — постобработкой (встроенный meshopt не квантует)
)

PRESETS = {
    # 1. Статичный hero-объект (витрина, первый экран)
    "static_hero": dict(BASE_WEB),
    # 2. Анимация трансформаций (объекты/пустышки): клипы из действий
    "anim_trs": dict(BASE_WEB, export_animations=True, export_animation_mode="ACTIONS", export_force_sampling=True,
                     export_frame_step=1, export_optimize_animation_size=True, export_anim_slide_to_zero=True,
                     export_bake_animation=False, export_merge_animation="ACTION"),
    # 3. Морф-анимация (shape keys): БЕЗ применения модификаторов
    "anim_morph": dict(BASE_WEB, export_apply=False, export_animations=True, export_animation_mode="ACTIONS",
                       export_morph=True, export_morph_normal=True, export_morph_animation=True,
                       export_try_sparse_sk=True, export_anim_slide_to_zero=True),
    # 4. Скелетная анимация
    "anim_skin": dict(BASE_WEB, export_apply=False, export_animations=True, export_animation_mode="ACTIONS",
                      export_skins=True, export_influence_nb=4, export_def_bones=True, export_rest_position_armature=True,
                      export_anim_single_armature=True, export_anim_slide_to_zero=True),
    # 5. Сцена с инстансами (связанные дубликаты под одним родителем и/или GN-инстансы)
    "instances": dict(BASE_WEB, export_gpu_instances=True, export_gn_mesh=True),
    # 6. «Лёгкий» для телефона: картинки как есть (JPEG/PNG!) — KTX2 и ресайз делает gltfpack; WebP-вход gltfpack -tc НЕ перекодирует
    "mobile_light": dict(BASE_WEB, export_image_format="AUTO"),
    # 7. Адресуемые узлы: метки hotspot_*/cam_*, extras, клики по частям — база та же, что static_hero;
    #    держит постобработка (POST ниже), которая НЕ переименовывает и не удаляет пустышки/имена
    "addressable_nodes": dict(BASE_WEB),
}

# Постобработка (npm-пакеты — $DDD_HOME/node; нативный gltfpack для текстур — $DDD_HOME/bin/gltfpack-1.2/gltfpack; toktx для ktx2 —
# $DDD_HOME/bin/KTX-Software-4.4.2-Linux-x86_64/bin)
POST = {
    "static_hero": "npx gltf-transform optimize IN OUT --compress meshopt --texture-compress webp --texture-size 2048 --simplify false",
    "anim_trs": "npx gltf-transform optimize IN OUT --compress meshopt --texture-compress webp --flatten false --join false --simplify false",
    "anim_morph": "npx gltf-transform optimize IN OUT --compress meshopt --texture-compress webp --flatten false --join false --simplify false",
    "anim_skin": "npx gltf-transform optimize IN OUT --compress meshopt --texture-compress webp --flatten false --join false --simplify false",
    "instances": "npx gltf-transform optimize IN OUT --compress meshopt --texture-compress webp --flatten false --join false --simplify false",
    "mobile_light": "gltfpack -i IN -o OUT -cc -tc -ts 0.5",
    # -kn (keep node names) -ke (keep extras): без них gltfpack -cc переименовывает/удаляет пустышки
    "addressable_nodes": "gltfpack -i IN -o OUT -cc -kn -ke",
}


def export(path, preset, **overrides):
    import bpy, os
    kw = dict(PRESETS[preset] if isinstance(preset, str) else preset); kw.update(overrides)
    valid = {p.identifier for p in bpy.ops.export_scene.gltf.get_rna_type().properties}
    bad = [k for k in kw if k not in valid]
    if bad:
        raise KeyError(f"нет параметров {bad} в export_scene.gltf этой версии")
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    return bpy.ops.export_scene.gltf(filepath=os.path.abspath(path), **kw)

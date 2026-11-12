bl_info = {
    "name": "GLB Asset Validator & Batch Exporter",
    "author": "Herve Kubana",
    "version": (1, 0, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar (N) > Pipeline",
    "description": "Validates mesh topology, transforms, and UVs before batch exporting .glb assets.",
    "category": "Import-Export",
}

import os
import bpy
import bmesh
from mathutils import Vector


class VALIDATOR_PG_Item(bpy.types.PropertyGroup):
    obj_name: bpy.props.StringProperty(name="Object Name")
    issue: bpy.props.StringProperty(name="Issue")


class VALIDATOR_OT_RunCheck(bpy.types.Operator):
    bl_idname = "pipeline.validate_collection"
    bl_label = "Validate Active Collection"
    bl_description = "Check meshes in the active collection for transforms, UVs, N-gons, and non-manifold geometry"

    def execute(self, context):
        scene = context.scene
        scene.validator_issues.clear()

        collection = context.view_layer.active_layer_collection.collection
        mesh_objects = [obj for obj in collection.objects if obj.type == 'MESH']

        if not mesh_objects:
            self.report({'WARNING'}, "No mesh objects found in active collection.")
            return {'FINISHED'}

        for obj in mesh_objects:
            # 1. Check Unapplied Scale
            if (obj.scale - Vector((1.0, 1.0, 1.0))).length > 0.0001:
                item = scene.validator_issues.add()
                item.obj_name = obj.name
                item.issue = "Unapplied Scale"

            # 2. Check Unapplied Rotation
            if Vector(obj.rotation_euler).length > 0.0001:
                item = scene.validator_issues.add()
                item.obj_name = obj.name
                item.issue = "Unapplied Rotation"

            # 3. Check Missing UV Map
            if not obj.data.uv_layers:
                item = scene.validator_issues.add()
                item.obj_name = obj.name
                item.issue = "Missing UV Map"

            # 4. BMesh Topology Checks (Non-Manifold & N-gons)
            bm = bmesh.new()
            bm.from_mesh(obj.data)
            bm.edges.ensure_lookup_table()
            bm.faces.ensure_lookup_table()

            non_manifold = [e for e in bm.edges if not e.is_manifold]
            if non_manifold:
                item = scene.validator_issues.add()
                item.obj_name = obj.name
                item.issue = f"Non-Manifold Edges ({len(non_manifold)})"

            ngons = [f for f in bm.faces if len(f.verts) > 4]
            if ngons:
                item = scene.validator_issues.add()
                item.obj_name = obj.name
                item.issue = f"N-gons Detected ({len(ngons)})"

            bm.free()

        if len(scene.validator_issues) == 0:
            self.report({'INFO'}, f"All {len(mesh_objects)} meshes passed validation!")
        else:
            self.report({'WARNING'}, f"Found {len(scene.validator_issues)} issue(s) in collection.")

        return {'FINISHED'}


class VALIDATOR_OT_SelectObject(bpy.types.Operator):
    bl_idname = "pipeline.select_flagged_object"
    bl_label = "Select Object"
    bl_description = "Select and focus the flagged object in the viewport"

    target_name: bpy.props.StringProperty()

    def execute(self, context):
        bpy.ops.object.select_all(action='DESELECT')
        obj = bpy.data.objects.get(self.target_name)
        if obj:
            obj.select_set(True)
            context.view_layer.objects.active = obj
        return {'FINISHED'}


class VALIDATOR_OT_BatchExportGLB(bpy.types.Operator):
    bl_idname = "pipeline.batch_export_glb"
    bl_label = "Batch Export Collection to GLB"
    bl_description = "Export each mesh in the active collection as an individual .glb file"

    def execute(self, context):
        export_dir = bpy.path.abspath(context.scene.validator_export_path)
        if not export_dir:
            self.report({'ERROR'}, "Please set a valid export folder path.")
            return {'CANCELLED'}

        try:
            os.makedirs(export_dir, exist_ok=True)
        except Exception as e:
            self.report({'ERROR'}, f"Failed to create export folder: {e}")
            return {'CANCELLED'}

        collection = context.view_layer.active_layer_collection.collection
        mesh_objects = [obj for obj in collection.objects if obj.type == 'MESH']

        if not mesh_objects:
            self.report({'WARNING'}, "No meshes to export in active collection.")
            return {'CANCELLED'}

        bpy.ops.object.select_all(action='DESELECT')
        exported_count = 0

        for obj in mesh_objects:
            obj.select_set(True)
            context.view_layer.objects.active = obj
            filepath = os.path.join(export_dir, f"{obj.name}.glb")

            bpy.ops.export_scene.gltf(
                filepath=filepath,
                use_selection=True,
                export_format='GLB',
                export_apply=True,
                export_texcoords=True,
                export_normals=True,
                export_materials='EXPORT',
            )
            obj.select_set(False)
            exported_count += 1

        self.report({'INFO'}, f"Exported {exported_count} GLB asset(s) to {export_dir}")
        return {'FINISHED'}


class VALIDATOR_PT_MainPanel(bpy.types.Panel):
    bl_label = "GLB Asset Validator"
    bl_idname = "VALIDATOR_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Pipeline'

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        col = layout.column(align=True)
        col.operator("pipeline.validate_collection", icon='CHECKMARK')

        if scene.validator_issues:
            box = layout.box()
            box.label(text=f"Issues Found ({len(scene.validator_issues)}):", icon='ERROR')
            for item in scene.validator_issues:
                row = box.row(align=True)
                row.label(text=f"{item.obj_name}: {item.issue}")
                op = row.operator("pipeline.select_flagged_object", text="", icon='RESTRICT_SELECT_OFF')
                op.target_name = item.obj_name
        else:
            layout.label(text="No active warnings.", icon='INFO')

        layout.separator()
        layout.prop(scene, "validator_export_path", text="Output")
        layout.operator("pipeline.batch_export_glb", icon='EXPORT')


classes = (
    VALIDATOR_PG_Item,
    VALIDATOR_OT_RunCheck,
    VALIDATOR_OT_SelectObject,
    VALIDATOR_OT_BatchExportGLB,
    VALIDATOR_PT_MainPanel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.validator_issues = bpy.props.CollectionProperty(type=VALIDATOR_PG_Item)
    bpy.types.Scene.validator_export_path = bpy.props.StringProperty(
        name="Export Folder",
        subtype='DIR_PATH',
        default="//exports/"
    )


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.validator_issues
    del bpy.types.Scene.validator_export_path


if __name__ == "__main__":
    register()

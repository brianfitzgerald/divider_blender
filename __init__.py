# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import bpy
from bpy.props import IntProperty, PointerProperty
import mathutils
import bmesh

bl_info = {
    "name" : "Divider",
    "author" : "Brian Fitzgerald",
    "description" : "",
    "blender" : (2, 80, 0),
    "version" : (0, 0, 1),
    "location" : "",
    "warning" : "",
    "category" : "Generic"
}

def main(context):
    obj = context.object
    verts = [vert.co for vert in obj.data.vertices]
    new_verts = []
    x = 0.5
    y = 0.5
    if bpy.context.mode == 'EDIT_MESH':
        bm = bmesh.from_edit_mesh(obj.data)
    else:
        bm = bmesh.new()
        bm.from_object(obj, context.scene)
    subdivide(bm, verts, 5, new_verts, x, y)


def subdivide(bm, pv, level, new_verts, x, y):
    level_verts = []
    original_face = bm.faces[0]
    if level == 0:
        return
    else:

        pos_a = pv[0].lerp(pv[1], y)
        pos_b = pv[1].lerp(pv[2], x)
        pos_c = pv[3].lerp(pv[2], 1-y)
        pos_d = pv[0].lerp(pv[3], x)

        pos_e = pos_d.lerp(pos_b, y)
        pos_f = pos_d.lerp(pos_b, 1-y)

        new_points = {
            "a": pos_a,
            "b": pos_b,
            "c": pos_c,
            "d": pos_d,
            "e": pos_e,
            "f": pos_f
        }
        new_verts = {}

        for i, (k, v) in enumerate(new_points):
            new_verts[k] = bm.verts.new(v)

        bm.faces.new([pv[0], new_verts["a"], new_verts["e"], new_verts["d"]])
        bm.faces.new([new_verts["a"], pv[1], new_verts["b"], new_verts["e"]])
        bm.faces.new([new_verts["b"], pv[2], new_verts["c"], new_verts["f"]])
        bm.faces.new([new_verts["d"], new_verts["f"], new_verts["c"], pv[3]])

        bmesh.ops.delete(bm, geom=original_face, context=5)

class DividerOperator(bpy.types.Operator):
    bl_idname = "object.divider_operator"
    bl_label = "Recursive Subdivide Object"

    num_subdivisions = bpy.props.IntProperty(
        name="Num Subdivs",
        min=0,
        max=1000
    )

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        main(context)
        print(self.num_subdivisions)
        return {'FINISHED'}

class DividerPanel(bpy.types.Panel):
    bl_idname = "panel.divider"
    bl_label = "Divider"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Divider"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        op = layout.operator(DividerOperator.bl_idname)
        op.num_subdivisions = scene.div_settings.num_subdivisions
        obj = context.object

        layout.prop(scene.div_settings, "num_subdivisions")

class DividerSettings(bpy.types.PropertyGroup):
    num_subdivisions = bpy.props.IntProperty(
        name="Num Subdivs",
        min=1,
        max=1000
    )

def register():
    bpy.utils.register_class(DividerSettings)
    bpy.types.Scene.div_settings = PointerProperty(type=DividerSettings)
    bpy.utils.register_class(DividerOperator)
    bpy.utils.register_class(DividerPanel)


def unregister():
    bpy.utils.unregister_class(DividerSettings)
    bpy.utils.unregister_class(DividerOperator)
    bpy.utils.unregister_class(DividerPanel)
    del(bpy.types.Scene.div_settings)

if __name__ == "__main__":
    register()
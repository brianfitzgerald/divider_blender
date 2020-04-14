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

def main(context, num_subdivisions):
    obj = context.object
    x = 0.3
    y = 0.3
    if bpy.context.mode == 'EDIT_MESH':
        bm = bmesh.from_edit_mesh(obj.data)
    else:
        bm = bmesh.new()
        bm.from_mesh(obj.data)
    subdivide(obj, bm, obj.data.vertices, num_subdivisions, x, y)


def subdivide(obj, bm, pv, level, x, y):
    pv_co = [vert.co for vert in pv]
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    if level == 0:
        return
    else:

        # pos x - top
        pos_a = pv_co[2].lerp(pv_co[3], x)
        # pos y - right
        pos_b = pv_co[3].lerp(pv_co[1], y)
        # neg x - bottom
        pos_c = pv_co[0].lerp(pv_co[1], 1-x)
        # neg y - left
        pos_d = pv_co[2].lerp(pv_co[0], y)

        
        pos_e = pos_d.lerp(pos_b, y)
        # center
        pos_f = pos_d.lerp(pos_b, 1-y)

        new_points = {
            "a": pos_a,
            "b": pos_b,
            "c": pos_c,
            "d": pos_d,
            "e": pos_e,
            "f": pos_f,
            "0": pv_co[0],
            "1": pv_co[1],
            "2": pv_co[2],
            "3": pv_co[3],
        }
        new_verts = {}

        for key in new_points:
            new_verts[key] = bm.verts.new(new_points[key])

        
        faces = [
            [new_verts["0"], new_verts["c"], new_verts["f"], new_verts["d"]],
            [new_verts["a"], new_verts["2"], new_verts["d"], new_verts["e"]],
            [new_verts["e"], new_verts["b"], new_verts["3"], new_verts["a"]],
            [new_verts["1"], new_verts["c"], new_verts["f"], new_verts["b"]]
        ]

        for face in faces:
            bm.faces.new(face)
            print([f.co for f in face])
            subdivide(obj, bm, face, level-1, x, y)

        bmesh.update_edit_mesh(obj.data)


class DividerOperator(bpy.types.Operator):
    bl_idname = "object.divider_operator"
    bl_label = "Recursive Subdivide Object"

    num_subdivisions = bpy.props.IntProperty(
        name="Num Subdivs",
        min=1,
        max=50
    )

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        main(context, self.num_subdivisions)
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
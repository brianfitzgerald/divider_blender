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
import random

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

def main(context, num_subdivisions, x_offset, y_offset):
    obj = context.object
    if bpy.context.mode == 'EDIT_MESH':
        bm = bmesh.from_edit_mesh(obj.data)
    else:
        bm = bmesh.new()
        bm.from_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    x = 0.4
    y = 0.4
    subdivide(bm, obj.data.vertices, num_subdivisions, x, y)
    bmesh.update_edit_mesh(obj.data)


def subdivide(bm, pv, level, x, y):
    pv_co = [vert.co for vert in pv]
    print('sub', pv_co, level)
    if level == 0:
        return
    else:

        # pos x - top
        top = pv_co[2].lerp(pv_co[3], x)
        # pos y - right
        right = pv_co[3].lerp(pv_co[1], y)
        # neg x - bottom
        bottom = pv_co[0].lerp(pv_co[1], 1-x)
        # neg y - left
        left = pv_co[2].lerp(pv_co[0], y)

        
        pos_e = left.lerp(right, y)
        # center
        pos_f = left.lerp(right, 1-y)

        new_points = {
            "top": top,
            "right": right,
            "bottom": bottom,
            "left": left,
            "mid_pos": pos_e,
            "mid_neg": pos_f,
            "0": pv_co[0],
            "1": pv_co[1],
            "2": pv_co[2],
            "3": pv_co[3],
        }
        new_verts = {}

        for key in new_points:
            print(key, new_points[key])
            new_verts[key] = bm.verts.new(new_points[key])

        faces = [
            # bottom left, bottom, center, left
            [new_verts["0"], new_verts["bottom"], new_verts["mid_neg"], new_verts["left"]],
            [new_verts["top"], new_verts["2"], new_verts["left"], new_verts["mid_pos"]],
            [new_verts["mid_pos"], new_verts["right"], new_verts["3"], new_verts["top"]],
            [new_verts["1"], new_verts["bottom"], new_verts["mid_neg"], new_verts["right"]]
        ]

        for face in faces:
            new_verts = bm.faces.new(face).verts
            bm.verts.ensure_lookup_table()
            bm.faces.ensure_lookup_table()
            nv = [new_verts[0], new_verts[1], new_verts[3], new_verts[2]]
            subdivide(bm, nv, level-1, x, y)

def rotate(l, n): return l[n:] + l[:n]

def sort(verts):
    sorted = []
    for x in range(len(verts)):
        sorted.append(verts[len(verts)-x-1])
    return sorted


class DividerOperator(bpy.types.Operator):
    bl_idname = "object.divider_operator"
    bl_label = "Recursive Subdivide Object"

    num_subdivisions = bpy.props.IntProperty(
        name="Num Subdivs",
        min=1,
        max=50
    )

    x_offset = bpy.props.FloatProperty(
        name=" Offset",
        min=0,
        max=1
    )

    y_offset = bpy.props.FloatProperty(
        name="Y Offset",
        min=0,
        max=1
    )

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        main(context, self.num_subdivisions, self.x_offset, self.y_offset)
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
        layout.prop(scene.div_settings, "x_offset")
        layout.prop(scene.div_settings, "y_offset")

class DividerSettings(bpy.types.PropertyGroup):
    num_subdivisions = bpy.props.IntProperty(
        name="Num Subdivs",
        min=1,
        max=1000
    )

    x_offset = bpy.props.FloatProperty(
        name=" Offset",
        min=0,
        max=1
    )

    y_offset = bpy.props.FloatProperty(
        name="Y Offset",
        min=0,
        max=1
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
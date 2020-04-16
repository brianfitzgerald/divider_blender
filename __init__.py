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
from mathutils import Vector


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

def main(context, num_subdivisions, offset, extrude):
    obj = context.object
    animate = True
    decoy = obj.copy()
    decoy.data = obj.data.copy()
    bpy.context.scene.collection.objects.link(decoy)
    basis = create_offset_bmesh(context, obj, num_subdivisions, offset, extrude)
    basis.to_mesh(obj.data)
    if animate:
        # end frame
        begin_frame = obj.shape_key_add(name="begin")
        end_frame = obj.shape_key_add(name="end")
        begin_frame.interpolation = 'KEY_LINEAR'
        end_frame.interpolation = 'KEY_LINEAR'
        animated = create_offset_bmesh(context, decoy, num_subdivisions, 0.5, extrude)
        animated.to_mesh(decoy.data)
        basis.verts.ensure_lookup_table()
        animated.verts.ensure_lookup_table()
        basis.to_mesh(obj.data)
        for i in range(len(basis.verts)):
            end_frame.data[i].co = animated.verts[i].co
            begin_frame.data[i].co = basis.verts[i].co
        animated.to_mesh(decoy.data)

def create_offset_bmesh(context, obj, num_subdivisions, offset, extrude):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    all_faces = []
    subdivide(bm, obj.data.vertices, bm.faces[0], num_subdivisions, offset, all_faces)
    if extrude:
        for face in all_faces:
            r = bmesh.ops.extrude_discrete_faces(bm, faces=[face])
            extrude_height = random.uniform(0.5, 1)
            verts_to_translate = r['faces'][0].verts
            bmesh.ops.translate( bm, vec = Vector((0,0,extrude_height)), verts=verts_to_translate)
    return bm

def subdivide(bm, pv, parent_face, level, offset, all_faces):
    pv_co = [vert.co for vert in pv]
    if level == 0:
        all_faces.append(parent_face)
        return
    else:

        # pos x - top
        top = pv_co[2].lerp(pv_co[3], offset)
        # pos y - right
        right = pv_co[3].lerp(pv_co[1], offset)
        # neg x - bottom
        bottom = pv_co[0].lerp(pv_co[1], 1-offset)
        # neg y - left
        left = pv_co[2].lerp(pv_co[0], offset)

        pos_e = left.lerp(right, offset)
        # center
        pos_f = left.lerp(right, 1-offset)

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
            new_verts[key] = bm.verts.new(new_points[key])

        faces = [
            # bottom left, bottom, center, left
            [new_verts["0"], new_verts["bottom"], new_verts["mid_neg"], new_verts["left"]],
            [new_verts["top"], new_verts["2"], new_verts["left"], new_verts["mid_pos"]],
            [new_verts["mid_pos"], new_verts["right"], new_verts["3"], new_verts["top"]],
            [new_verts["1"], new_verts["bottom"], new_verts["mid_neg"], new_verts["right"]]
        ]

        bm.faces.remove(parent_face)

        for face in faces:
            new_face = bm.faces.new(face)
            new_verts = new_face.verts
            bm.verts.ensure_lookup_table()
            bm.faces.ensure_lookup_table()
            nv = [new_verts[0], new_verts[1], new_verts[3], new_verts[2]]
            subdivide(bm, nv, new_face, level-1, offset, all_faces)

def rotate(l, n): return l[n:] + l[:n]

def sort(verts):
    sorted = []
    for x in range(len(verts)):
        sorted.append(verts[len(verts)-x-1])
    return sorted


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
        op.offset = scene.div_settings.offset

        layout.prop(scene.div_settings, "num_subdivisions")
        layout.prop(scene.div_settings, "offset")
        layout.prop(scene.div_settings, "extrude")

class DividerOperator(bpy.types.Operator):
    bl_idname = "object.divider_operator"
    bl_label = "Recursive Subdivide Object"

    num_subdivisions = bpy.props.IntProperty(
        name="Num Subdivs",
        min=1,
        max=50
    )

    offset = bpy.props.FloatProperty(
        name="Offset",
        min=0,
        max=1,
        default=0.3
    )

    extrude = bpy.props.BoolProperty(
        name="Extrude After Subdivide",
        default=True
    )

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        main(context, self.num_subdivisions, self.offset, self.extrude)
        return {'FINISHED'}

class DividerSettings(bpy.types.PropertyGroup):
    num_subdivisions = bpy.props.IntProperty(
        name="Num Subdivs",
        min=1,
        max=1000
    )

    offset = bpy.props.FloatProperty(
        name="Offset",
        min=0,
        max=1,
        default=0.3
    )

    extrude = bpy.props.BoolProperty(
        name="Extrude After Subdivide",
        default=True
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
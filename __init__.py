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
    "name": "Divider",
    "author": "Brian Fitzgerald",
    "description": "",
    "blender": (2, 80, 0),
    "version": (0, 0, 1),
    "location": "",
    "warning": "",
    "category": "Generic"
}


random_seed = 401


def ShowMessageBox(message="", title="Message Box", icon='INFO'):

    def draw(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)


def main(context, op):
    obj = context.object

    print(op.subbed_meshes)

    if obj in op.subbed_meshes:
        ShowMessageBox(
            "This mesh has been subdivided already, try a different one or delete this one.")
        return

    op.subbed_meshes.append(obj)

    decoy = obj.copy()
    decoy.data = obj.data.copy()
    bpy.context.scene.collection.objects.link(decoy)
    basis = create_offset_bmesh(
        context, obj, op.num_subdivisions, op.offset, op.extrude_style, 0)
    basis.to_mesh(obj.data)

    print(op.create_noise_keyframes, op.animate, op.create_keyframes)

    if op.create_noise_keyframes and not (op.animate and op.create_keyframes):
        ShowMessageBox(
            "Please check 'Animate' and 'Create Keyframes' if you want to use noise keyframes!")
        return

    if op.animate:
        # Create bmeshes for animation
        begin_frame = obj.shape_key_add(name="begin")
        end_frame = obj.shape_key_add(name="end")
        begin_frame.interpolation = 'KEY_LINEAR'
        end_frame.interpolation = 'KEY_LINEAR'
        animated = create_offset_bmesh(
            context, decoy, op.num_subdivisions, op.animation_end_offset, op.extrude_style, 1)
        animated.to_mesh(decoy.data)

        basis.verts.ensure_lookup_table()
        animated.verts.ensure_lookup_table()

        basis.to_mesh(obj.data)
        # create shape keys
        for i in range(len(basis.verts)):
            end_frame.data[i].co = animated.verts[i].co
            begin_frame.data[i].co = basis.verts[i].co
        # delete decoy bmesh
        animated.to_mesh(decoy.data)
        bpy.data.objects.remove(decoy)


def create_offset_bmesh(context, obj, num_subdivisions, offset, extrude_style, offset_index):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    all_faces = []
    subdivide(bm, obj.data.vertices,
              bm.faces[0], num_subdivisions, offset, all_faces)
    if extrude_style != 'flat':
        faces = bm.faces
        # Once faces are being extruded, this is the range they use to translate
        random_range = [[0.5, 1]]
        areas = []
        for face in faces:
            area = face.calc_area()
            areas.append(area)
        areas.sort(reverse=False)
        distribution = [1]
        if extrude_style == 'hilly':
            distribution = [2, 1]
            random_range = [[0], [0.02, 0.05]]
        if extrude_style == 'towers':
            distribution = [0, 3, 1]
            random_range = [[0], [0.5, 1], [1, 2]]
        if extrude_style == 'ultratowers':
            distribution = [6, 1]
            random_range = [[0], [2, 2.5]]
        distribution_points = []
        while len(distribution_points) < len(faces):
            for i in range(len(distribution)):
                for x in range(distribution[i]):
                    print('x', x)
                    distribution_points.append(random_range[i])
        random.Random(random_seed).shuffle(distribution_points)
        for x in range(len(faces)):
            bm.faces.ensure_lookup_table()
            area = faces[x].calc_area()
            face = faces[x]
            range_for_face = distribution_points[x]
            if len(range_for_face) == 1:
                continue
            r = bmesh.ops.extrude_discrete_faces(bm, faces=[face])
            extrude_height = random.uniform(
                range_for_face[0], range_for_face[1])
            if extrude_style == "evenodd":
                even = x % 2 == 0
                if offset_index == 0:
                    extrude_height = 0.5 if even else 1
                else:
                    extrude_height = 1 if even else 0.5
            verts_to_translate = r['faces'][0].verts
            bmesh.ops.translate(bm, vec=Vector(
                (0, 0, extrude_height)), verts=verts_to_translate)
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
            [new_verts["0"], new_verts["bottom"],
                new_verts["mid_neg"], new_verts["left"]],
            [new_verts["top"], new_verts["2"],
                new_verts["left"], new_verts["mid_pos"]],
            [new_verts["mid_pos"], new_verts["right"],
                new_verts["3"], new_verts["top"]],
            [new_verts["1"], new_verts["bottom"],
                new_verts["mid_neg"], new_verts["right"]]
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

        layout.prop(scene.div_settings, "num_subdivisions")
        layout.prop(scene.div_settings, "offset")

        layout.label(text="Animation")
        layout.prop(scene.div_settings, "animate")
        layout.prop(scene.div_settings, "create_keyframes")
        layout.prop(scene.div_settings, "start_keyframe")
        layout.prop(scene.div_settings, "end_keyframe")
        layout.prop(scene.div_settings,
                    "animation_end_offset")
        layout.prop(scene.div_settings,
                    "create_noise_keyframes")

        layout.label(text="Extrude Style")
        layout.prop(scene.div_settings, "extrude_style", text="")

        layout.operator(CreatePlaneOperator.bl_idname)

        op = layout.operator(DividerOperator.bl_idname)
        op.num_subdivisions = scene.div_settings.num_subdivisions
        op.offset = scene.div_settings.offset
        op.animation_end_offset = scene.div_settings.animation_end_offset
        op.extrude_style = scene.div_settings.extrude_style
        op.create_noise_keyframes = scene.div_settings.create_noise_keyframes
        op.animate = scene.div_settings.animate
        op.create_keyframes = scene.div_settings.create_keyframes


extrude_style_options = [
    ('flat', 'Flat', 'No extrusion'),
    ('random', 'Random', 'Evently distributed random extrusion'),
    ('hilly', 'Hilly', 'Larger sections are given a short extrusion'),
    ('towers', 'Towers', 'Even distribution with some made very tall'),
    ('ultratowers', 'Ultra Towers', 'Only occasional very tall extrusions'),
    ('evenodd', 'Even / Odd',
     'Each surface is given an inverse extrusion on the first/last frame'),
]


class DividerOperator(bpy.types.Operator):
    bl_idname = "object.divider_operator"
    bl_label = "Recursive Subdivide Object"

    num_subdivisions = bpy.props.IntProperty(
        name="Num Subdivs",
        min=1,
        max=50,
        default=3
    )

    offset = bpy.props.FloatProperty(
        name="Offset",
        min=0,
        max=1,
        default=0.3
    )

    animation_end_offset = bpy.props.FloatProperty(
        name="Animation End Offset",
        min=0,
        max=1,
        default=0.8
    )

    extrude_style = bpy.props.EnumProperty(
        name="Extrude Style",
        items=extrude_style_options
    )

    animate = bpy.props.BoolProperty(
        name="Animate",
        default=True
    )

    create_keyframes = bpy.props.BoolProperty(
        name="Create Keyframes",
        default=True
    )

    start_keyframe = bpy.props.IntProperty(
        name="Start Keyframe",
        default=0
    )

    end_keyframe = bpy.props.IntProperty(
        name="End Keyframe",
        default=250
    )

    create_noise_keyframes = bpy.props.BoolProperty(
        name="Create Noise Keyframes",
        default=False
    )

    subbed_meshes = []

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        main(context, self)
        return {'FINISHED'}


class CreatePlaneOperator(bpy.types.Operator):
    bl_idname = "object.create_plane_operator"
    bl_label = "Create Plane"

    @classmethod
    def poll(cls, context):
        if not context.active_object:
            return True
        return context.active_object.mode == 'OBJECT'

    def execute(self, context):
        bpy.ops.mesh.primitive_plane_add(size=5)
        return {'FINISHED'}


class DividerSettings(bpy.types.PropertyGroup):
    num_subdivisions = bpy.props.IntProperty(
        name="Num Subdivs",
        min=1,
        max=1000,
        default=3
    )

    offset = bpy.props.FloatProperty(
        name="Offset",
        min=0,
        max=1,
        default=0.3
    )

    animation_end_offset = bpy.props.FloatProperty(
        name="Animation End Offset",
        min=0,
        max=1,
        default=0.8
    )

    extrude_style = bpy.props.EnumProperty(
        name="Extrude Style",
        items=extrude_style_options
    )

    animate = bpy.props.BoolProperty(
        name="Animate",
        default=True
    )

    create_keyframes = bpy.props.BoolProperty(
        name="Create Keyframes",
        default=True
    )

    start_keyframe = bpy.props.IntProperty(
        name="Start Keyframe",
        default=0
    )

    end_keyframe = bpy.props.IntProperty(
        name="End Keyframe",
        default=250
    )

    create_noise_keyframes = bpy.props.BoolProperty(
        name="Create Noise Keyframes",
        default=False
    )


def register():
    bpy.utils.register_class(DividerSettings)
    bpy.types.Scene.div_settings = PointerProperty(type=DividerSettings)
    bpy.utils.register_class(DividerOperator)
    bpy.utils.register_class(CreatePlaneOperator)
    bpy.utils.register_class(DividerPanel)


def unregister():
    bpy.utils.unregister_class(DividerSettings)
    bpy.utils.unregister_class(DividerOperator)
    bpy.utils.unregister_class(CreatePlaneOperator)
    bpy.utils.unregister_class(DividerPanel)
    del(bpy.types.Scene.div_settings)


if __name__ == "__main__":
    register()

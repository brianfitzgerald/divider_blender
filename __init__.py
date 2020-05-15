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

    if obj in op.subbed_meshes:
        ShowMessageBox(
            "This mesh has been subdivided already, try a different one or delete this one.")
        return

    op.subbed_meshes.append(obj)
    shape_keys = []
    if op.animate:
        # Important that this is not modified as it's used for each interpolation.
        original_mesh = obj.copy()
        original_mesh.data = obj.data.copy()
        # Basis is the first frame of the subdiv mesh.
        basis = create_offset_bmesh(
            context, obj, op, 0, False)
        basis.to_mesh(obj.data)
        num_frames = op.num_keyframes
        # Create bmeshes for animation
        for index in range(num_frames):
            frame = create_shape_key_with_offset(
                context, op, obj, basis, original_mesh, index, num_frames)
            shape_keys.append(frame)
    else:
        offset_mesh = create_offset_bmesh(context, obj, op, op.offset, 0)
        offset_mesh.to_mesh(obj.data)
        bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
        return

    if op.animate:
        keyframe_interval = op.keyframe_interval
        for frame in range(len(shape_keys) * keyframe_interval):
            for index in range(len(shape_keys)):
                if frame % keyframe_interval == 0:
                    if frame / keyframe_interval == index:
                        shape_keys[index].value = 1
                    else:
                        shape_keys[index].value = 0
                    frame_val = frame + 1 if frame == 0 else frame
                    shape_keys[index].keyframe_insert("value", frame=frame_val)
        bpy.context.scene.frame_start = 1
        bpy.context.scene.frame_end = (
            len(shape_keys) - 1) * keyframe_interval

        bpy.data.objects.remove(original_mesh)


# Create a new shape kaey starting with the original mesh data and generating a new subdiv with a specific offset.
# This creates new geometry each time.
# Apply only one keyframe at a time, as they're all relative to each other!
def create_shape_key_with_offset(context, op, obj, basis, original_mesh, frame_index, total_frames):
    #
    decoy = original_mesh.copy()
    decoy.data = original_mesh.data.copy()
    bpy.context.scene.collection.objects.link(decoy)

    offset_amount = op.offset + \
        (frame_index / total_frames) * \
        (op.animation_end_offset - op.offset)
    offset_amount = round(offset_amount, 2)

    offset_bmesh = create_offset_bmesh(
        context, decoy, op, offset_amount, frame_index)

    basis.verts.ensure_lookup_table()
    offset_bmesh.verts.ensure_lookup_table()

    keyframe_name = "Frame {}".format(frame_index)
    frame = obj.shape_key_add(name=keyframe_name)
    frame.interpolation = 'KEY_LINEAR'

    # Take the offset mesh and apply it to decoy
    offset_bmesh.to_mesh(decoy.data)
    for i in range(len(basis.verts)):
        frame.data[i].co = offset_bmesh.verts[i].co
    bpy.data.objects.remove(decoy)
    return frame


# Creates a full mesh with a specific amount of offset.
def create_offset_bmesh(context, obj, op, offset, frame_index):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    all_faces = []
    subdivide(bm, obj.data.vertices,
              bm.faces[0], op.num_subdivisions, offset, all_faces, op.add_noise, op.noise_amount)
    extrude_style = op.extrude_style
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
                    distribution_points.append(random_range[i])
        random.Random(random_seed).shuffle(distribution_points)
        for x in range(len(faces)):
            bm.faces.ensure_lookup_table()
            area = faces[x].calc_area()
            face = faces[x]
            norm = face.normal
            range_for_face = distribution_points[x]
            if len(range_for_face) == 1:
                continue
            r = bmesh.ops.extrude_discrete_faces(bm, faces=[face])
            extrude_height = random.uniform(
                range_for_face[0], range_for_face[1])
            extrude_vector = norm * \
                extrude_height if op.use_normal_direction else Vector((
                    0, 0, extrude_height))
            if extrude_style == "evenodd":
                even = x % 2 == 0
                if frame_index == 0:
                    extrude_height = 0.5 if even else 1
                else:
                    extrude_height = 1 if even else 0.5
            verts_to_translate = r['faces'][0].verts
            bmesh.ops.translate(bm, vec=extrude_vector,
                                verts=verts_to_translate)
    return bm


def clamp(value, lower, upper):
    return lower if value < lower else upper if value > upper else value


def subdivide(bm, pv, parent_face, level, offset, all_faces, add_noise, noise_amount):
    if add_noise:
        noise_val = random.uniform(noise_amount * -1, noise_amount) * 0.5
        offset += noise_val
        offset = clamp(offset, 0, 1)
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
            subdivide(bm, nv, new_face, level-1, offset,
                      all_faces, add_noise, noise_amount)


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
        layout.prop(scene.div_settings, "keyframe_interval")
        layout.prop(scene.div_settings, "num_keyframes")
        layout.prop(scene.div_settings,
                    "animation_end_offset")
        layout.prop(scene.div_settings,
                    "add_noise")

        layout.prop(scene.div_settings,
                    "noise_amount")

        layout.label(text="Extrude Style")
        layout.prop(scene.div_settings, "extrude_style", text="")
        layout.prop(scene.div_settings, "use_normal_direction")

        layout.operator(CreatePlaneOperator.bl_idname)

        op = layout.operator(DividerOperator.bl_idname)
        op.num_subdivisions = scene.div_settings.num_subdivisions
        op.offset = scene.div_settings.offset
        op.animation_end_offset = scene.div_settings.animation_end_offset
        op.extrude_style = scene.div_settings.extrude_style
        op.add_noise = scene.div_settings.add_noise
        op.animate = scene.div_settings.animate
        op.keyframe_interval = scene.div_settings.keyframe_interval
        op.noise_amount = scene.div_settings.noise_amount
        op.num_keyframes = scene.div_settings.num_keyframes
        op.use_normal_direction = scene.div_settings.use_normal_direction


extrude_style_options = [
    ('random', 'Random', 'Evently distributed random extrusion'),
    ('flat', 'Flat', 'No extrusion'),
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

    start_keyframe = bpy.props.IntProperty(
        name="Start Keyframe",
        default=0
    )

    end_keyframe = bpy.props.IntProperty(
        name="End Keyframe",
        default=250
    )

    add_noise = bpy.props.BoolProperty(
        name="Add Noise",
        default=False
    )

    use_normal_direction = bpy.props.BoolProperty(
        name="Use Face Normals",
        default=False
    )

    noise_amount = bpy.props.FloatProperty(
        name="Noise Amount",
        default=0.2,
        min=0,
        max=1
    )

    keyframe_interval = bpy.props.IntProperty(
        name="Keyframe Interval",
        default=20
    )

    num_keyframes = bpy.props.IntProperty(
        name="# of Keyframes",
        default=5
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

    add_noise = bpy.props.BoolProperty(
        name="Add Noise",
        default=False
    )

    noise_amount = bpy.props.FloatProperty(
        name="Noise Amount",
        default=0.2,
        min=0,
        max=1
    )

    keyframe_interval = bpy.props.IntProperty(
        name="Keyframe Interval",
        default=20
    )

    num_keyframes = bpy.props.IntProperty(
        name="Number of Keyframes",
        default=5
    )

    use_normal_direction = bpy.props.BoolProperty(
        name="Extrude Along Normal",
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

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
    for ob in context.scene.objects:
        print(ob)


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
        min=0,
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
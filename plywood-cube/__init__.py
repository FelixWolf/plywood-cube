# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
    "name": "Plywood Cube",
    "category": "System",
    "author": "Félix",
    "version": (2, 0, 1),
    "blender": (3, 1, 2),
    "location": "View3D > Add > Second Life Rig",
    "description": "Various Second Life tools"
}

import bpy
import importlib
# noinspection PyUnresolvedReferences
from bpy.props import (
    BoolProperty,
    FloatVectorProperty,
    IntProperty,
    FloatProperty,
    StringProperty,
)
# noinspection PyUnresolvedReferences
from bpy.types import (
    Operator,
    Menu
)
from bpy_extras.object_utils import AddObjectHelper, object_data_add
from . import sl_skeleton
from . import sl_avatar
from . import puppetry
from . import tools

#Avatar
##Skeleton
class OBJECT_OT_add_secondlife_skeleton(Operator, AddObjectHelper):
    """Create a new Mesh Object"""
    bl_idname = "add.secondlife_skeleton"
    bl_label = "Skeleton"
    bl_options = {'REGISTER', 'UNDO'}

    scale: FloatVectorProperty(
        name="scale",
        default=(1.0, 1.0, 1.0),
        subtype='TRANSLATION',
        description="scaling",
    )

    def execute(self, context):
        sl_skeleton.add_skeleton(self, context)
        return {'FINISHED'}

##Avatar
class OBJECT_OT_add_secondlife_avatar(Operator, AddObjectHelper):
    """Create a new Mesh Object"""
    bl_idname = "add.secondlife_avatar"
    bl_label = "Avatar"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        arm, bone_matrix = sl_skeleton.add_skeleton(self, context)
        meshes = sl_avatar.attachMeshesToArmature(arm)
        return {'FINISHED'}


#Add menu
class VIEW3D_MT_secondlife_menu(Menu):
    bl_idname = "VIEW3D_MT_secondlife_menu"
    bl_label = "Second Life"

    # noinspection PyUnusedLocal
    def draw(self, context):
        self.layout.operator_context = 'INVOKE_REGION_WIN'
        self.layout.operator(OBJECT_OT_add_secondlife_skeleton.bl_idname, text="Skeleton", icon="ARMATURE_DATA")
        self.layout.operator(OBJECT_OT_add_secondlife_avatar.bl_idname, text="Avatar", icon="OUTLINER_OB_ARMATURE")
        #self.layout.separator()

module_classes = (
    VIEW3D_MT_secondlife_menu,
    OBJECT_OT_add_secondlife_skeleton,
    OBJECT_OT_add_secondlife_avatar,
)

def add_secondlife_menu_func(self, context):
    layout = self.layout
    layout.separator()
    self.layout.menu(VIEW3D_MT_secondlife_menu.bl_idname, icon="VIEW_PAN")

importlib.reload(sl_skeleton)
importlib.reload(sl_avatar)
importlib.reload(puppetry)
importlib.reload(tools)

def register():
    for cls in module_classes:
        bpy.utils.register_class(cls)
        
    bpy.types.VIEW3D_MT_add.append(add_secondlife_menu_func)
    
    tools.register()
    sl_skeleton.register()
    sl_avatar.register()
    puppetry.register()

def unregister():
    for cls in reversed(module_classes):
        bpy.utils.unregister_class(cls)
    
    bpy.types.VIEW3D_MT_add.append(add_secondlife_menu_func)
    
    tools.unregister()
    sl_skeleton.unregister()
    sl_avatar.unregister()
    puppetry.unregister()


if __name__ == "__main__":
    register()


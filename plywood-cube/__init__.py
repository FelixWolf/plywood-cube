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

from . import add_skeleton
from . import puppetry

importlib.reload(add_skeleton)
importlib.reload(puppetry)

def register():
    add_skeleton.register()
    puppetry.register()


def unregister():
    add_skeleton.unregister()
    puppetry.unregister()


if __name__ == "__main__":
    register()


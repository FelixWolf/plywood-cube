#!/usr/bin/env python3
import os.path
import struct
import math
import bpy

asset_path = os.path.join(os.path.dirname(__file__), "character")

BINARY_HEADER = b"Linden Binary Mesh 1.0\0\0"

sVec2 = struct.Struct("<2f")
sVec3 = struct.Struct("<3f")
sUInt16 = struct.Struct("<H")
sUInt16_3 = struct.Struct("<3H")
sUInt32 = struct.Struct("<I")
sUInt32_2 = struct.Struct("<2I")
sFloat = struct.Struct("<f")

class LindenMeshError(Exception):
    pass

def unpackFile(handle, lod = 0):
    header = handle.read(len(BINARY_HEADER))
    if header != BINARY_HEADER:
        raise LindenMeshError("Invalid Mesh Header!")
    
    readWeights = handle.read(1)[0] == 1 and not lod
    readDetailUVs = handle.read(1)[0] == 1
    
    position = sVec3.unpack(handle.read(sVec3.size))
    
    rotation = (*sVec3.unpack(handle.read(sVec3.size)), handle.read(1)[0])
    
    scale = sVec3.unpack(handle.read(sVec3.size))
    
    vertices = None
    normals = None
    binormals = None
    texcoords = None
    detailTexcoords = None
    weights = None
    
    if not lod:
        vCount, = sUInt16.unpack(handle.read(sUInt16.size))
        vertices = [None] * vCount
        for i in range(0, vCount):
            vertices[i] = sVec3.unpack(handle.read(sVec3.size))
        
        normals = [None] * vCount
        for i in range(0, vCount):
            normals[i] = sVec3.unpack(handle.read(sVec3.size))
        
        binormals = [None] * vCount
        for i in range(0, vCount):
            binormals[i] = sVec3.unpack(handle.read(sVec3.size))
        
        texcoords = [None] * vCount
        for i in range(0, vCount):
            texcoords[i] = sVec2.unpack(handle.read(sVec2.size))
        
        if readDetailUVs:
            detailTexcoords = [None] * vCount
            for i in range(0, vCount):
                detailTexcoords[i] = sVec2.unpack(handle.read(sVec2.size))
        
        if readWeights:
            weights = [None] * vCount
            for i in range(0, vCount):
                weights[i], = sFloat.unpack(handle.read(sFloat.size))
    
    
    fCount, = sUInt16.unpack(handle.read(sUInt16.size))
    faces = [None] * fCount
    maxIndice = 0
    for i in range(fCount):
        faces[i] = sUInt16_3.unpack(handle.read(sUInt16_3.size))
        
        if lod:
            maxIndice = max(maxIndice, max(faces[i]))
    
    joints = None
    morphs = None
    remaps = None
    if not lod:
        if readWeights:
            jCount, = sUInt16.unpack(handle.read(sUInt16.size))
            joints = [None] * jCount
            for i in range(jCount):
                jointName = handle.read(64)
                if len(jointName) != 64:
                    raise Exception("Unexpected end of joint data!")
                
                joints[i] = jointName.split(b"\0",1)[0].decode()
                
        morphs = {}
        while True:
            morphName = handle.read(64)
            if len(morphName) != 64:
                break
            
            morphName = morphName.split(b"\0",1)[0].decode()
            if morphName == "End Morphs":
                break
            
            mCount, = sUInt32.unpack(handle.read(sUInt32.size))
            
            morphIndices = [None] * mCount
            morphVertices = [None] * mCount
            morphNormals = [None] * mCount
            morphBinormals = [None] * mCount
            morphTexcoords = [None] * mCount
            
            for i in range(mCount):
                morphIndices[i], = sUInt32.unpack(handle.read(sUInt32.size))
                morphVertices[i] = sVec3.unpack(handle.read(sVec3.size))
                morphNormals[i] = sVec3.unpack(handle.read(sVec3.size))
                morphBinormals[i] = sVec3.unpack(handle.read(sVec3.size))
                morphTexcoords[i] = sVec2.unpack(handle.read(sVec2.size))
            
            morphs[morphName] = {
                "vertices": morphVertices,
                "normals": morphNormals,
                "binormals": morphBinormals,
                "texcoords": morphTexcoords,
                "indices": morphIndices
            }
        
        rCount, = sUInt32.unpack(handle.read(sUInt32.size))
        
        # Remaps are used to declare shared vertices when generating clothing
        # morphs. We don't need these, but get them just in case.
        # See indra/llappearance/llpolymorph.cpp
        remaps = {}
        for i in range(rCount):
            a, b = sUInt32_2.unpack(handle.read(sUInt32_2.size))
            remaps[a] = b
        
    return {
        "lod": lod,
        "position": position,
        "rotation": rotation,
        "scale": scale,
        "vertices": vertices,
        "normals": normals,
        "binormals": binormals,
        "texcoords": texcoords,
        "detailTexcoords": detailTexcoords,
        "weights": weights,
        "faces": faces,
        "joints": joints,
        "morphs": morphs,
        "remaps": remaps
    }

class LindenMeshMorph:
    def __init__(self, parent):
        self.parent = parent
        self.indices = []
        self.vertices = []
        self.normals = []
        self.binormals = []
        self.texcoords = []
    
    @classmethod
    def load(cls, data, parent):
        self = cls(parent)
        self.indices = data["indices"]
        self.vertices = data["vertices"]
        self.normals = data["normals"]
        self.binormals = data["binormals"]
        self.texcoords = data["texcoords"]
        return self

class LindenMeshLOD:
    def __init__(self, parent):
        self.parent = parent
        self.lod = 0
        self.position = (0,0,0)
        self.rotation = (0,0,0,0)
        self.scale = (0,0,0)
        self.faces = []
        self._vertices = []
        self._normals = []
        self._binormals = []
        self._texcoords = []
        self._detailTexcoords = []
        self._joints = []
        self._morphs = []
        self._remaps = []

    @classmethod
    def load(cls, data, parent):
        self = cls(parent)
        self.lod = data["lod"]
        self.position = data["position"]
        self.rotation = data["rotation"]
        self.scale = data["scale"]
        self.faces = data["faces"]
        
        #Proxied
        self._vertices = data["vertices"]
        self._normals = data["normals"]
        self._binormals = data["binormals"]
        self._texcoords = data["texcoords"]
        self._detailTexcoords = data["detailTexcoords"]
        self._weights = data["weights"]
        self._joints = data["joints"]
        self._morphs = {k: LindenMeshMorph.load(v, self) for k,v in data["morphs"].items()}
        self._remaps = data["remaps"]
        
        return self
    
    @property
    def vertices(self):
        if self._vertices:
            return self._vertices
        return self.parent.lods[0]._vertices
    
    @property
    def normals(self):
        if self._normals:
            return self._normals
        return self.parent.lods[0]._normals
    
    @property
    def binormals(self):
        if self._binormals:
            return self._binormals
        return self.parent.lods[0]._binormals
    
    @property
    def texcoords(self):
        if self._texcoords:
            return self._texcoords
        return self.parent.lods[0]._texcoords
    
    @property
    def detailTexcoords(self):
        if self._detailTexcoords:
            return self._detailTexcoords
        return self.parent.lods[0]._detailTexcoords
    
    @property
    def weights(self):
        if self._weights:
            return self._weights
        return self.parent.lods[0]._weights
    
    @property
    def joints(self):
        if self._joints:
            return self._joints
        return self.parent.lods[0]._joints
    
    @property
    def morphs(self):
        if self._morphs:
            return self._morphs
        return self.parent.lods[0]._morphs
    
    @property
    def remaps(self):
        if self._remaps:
            return self._remaps
        return self.parent.lods[0]._remaps
    

class LindenMesh:
    def __init__(self, name):
        self.name = name
        self.lods = []
    
    @classmethod
    def load(cls, path, loadLODs = False):
        self = cls(os.path.split(path)[-1])
        print(path)
        with open(path+".llm", "rb") as f:
            self.lods.append(LindenMeshLOD.load(unpackFile(f), self))
        
        if loadLODs:
            #Load all the LODs
            i = 1
            while True:
                try:
                    with open(path+"_{}.llm".format(i), "rb") as f:
                        self.lods.append(LindenMeshLOD.load(unpackFile(f, i), self))
                    i += 1
                
                except FileNotFoundError:
                    break
        
        return self

def buildJointPairs(armature_obj, joint_names):
    result = []

    # Make a lookup for bones by name
    bones_by_name = {b.name: b for b in armature_obj.data.bones}

    for name in joint_names:
        if name not in bones_by_name:
            print(f"[WARN] joint '{name}' not found in armature!")
            continue
        
        bone2_name = name
        while True:
            joint = bones_by_name[bone2_name]

            if joint.parent:
                bone2_name = joint.parent.name
                if bone2_name in joint_names:
                    break
            else:
                bone2_name = name  # root bone with no children
                break

        result.append((name, bone2_name))

    return result

def addLindenMesh(lm, lod = 0, armature = None):
    #Create the base data
    mesh = bpy.data.meshes.new(lm.name)
    obj = bpy.data.objects.new(mesh.name, mesh)
    col = bpy.data.collections["Collection"]
    col.objects.link(obj)
    
    #Import the vertices and faces
    mesh.from_pydata(lm.lods[lod].vertices, [], lm.lods[lod].faces)
    mesh.polygons.foreach_set("use_smooth", [True]*len(lm.lods[lod].faces))
    
    #Import UVs
    uv = obj.data.uv_layers.new(name='UVMap')
    for loop in obj.data.loops:
        uv.data[loop.index].uv = lm.lods[lod].texcoords[loop.vertex_index]
    
    #Import normal
    obj.data.normals_split_custom_set_from_vertices(lm.lods[lod].normals)
    
    #Add vertex groups
    if armature and lm.lods[lod].weights:
        vg_map = {}
        for joint in lm.lods[lod].joints:
            if joint not in obj.vertex_groups:
                vg_map[joint] = obj.vertex_groups.new(name=joint)
            else:
                vg_map[joint] = obj.vertex_groups[joint]
        
        jointMap = buildJointPairs(armature, lm.lods[lod].joints)
        # Now assign weights
        for vert, w in enumerate(lm.lods[lod].weights):
            if vert in lm.lods[lod].remaps:
                vert = lm.lods[lod].remaps[vert]
            
            boneIndex = int(math.floor(w))
            boneWeight = w - boneIndex
            
            boneIndex = boneIndex - 1
            try:
                vg1 = vg_map[jointMap[boneIndex][0]]
                vg1.add([vert], 1-boneWeight, "ADD")
            
                vg2 = vg_map[jointMap[boneIndex][1]]
                vg2.add([vert], boneWeight, "ADD")
            except Exception as e:
                print("Vert", vert)
                print(jointMap)
                print(boneIndex)
    
    #Add morphs
    if lm.lods[lod].morphs:
        sk = obj.shape_key_add(name="Basis", from_mix=True)
        sk.interpolation = 'KEY_LINEAR'
        for morph in lm.lods[lod].morphs:
            sk = obj.shape_key_add(name=morph, from_mix=False)
            sk.interpolation = 'KEY_LINEAR'
            for i in range(len(lm.lods[lod].morphs[morph].indices)):
                dest = lm.lods[lod].morphs[morph].indices[i]
                sk.data[dest].co = (
                    lm.lods[lod].morphs[morph].vertices[i][0] + lm.lods[lod].vertices[dest][0],
                    lm.lods[lod].morphs[morph].vertices[i][1] + lm.lods[lod].vertices[dest][1],
                    lm.lods[lod].morphs[morph].vertices[i][2] + lm.lods[lod].vertices[dest][2]
                )
    return obj

def attachMeshesToArmature(armature, meshes=None):
    #List of meshes to import
    if not meshes:
        meshes = [
            "avatar_upper_body",
            "avatar_lower_body",
            "avatar_head",
            "avatar_hair",
            "avatar_eyelashes",
            "avatar_eye", #One eye for each eye
            "avatar_eye",
            "avatar_skirt"
        ]
    
    eyed = 0 #Eye-D tracker, get it, ID, EyeD....
    
    added = []
    for mesh in meshes:
        lm = LindenMesh.load(os.path.join(asset_path, mesh))
        obj = addLindenMesh(lm, armature = armature)
        added.append(obj)
        
        #Don't parent anything if we don't have a armature selected
        if armature:
            obj.parent = armature
            
            #If we are adding eyes...
            if mesh == "avatar_eye":
                if eyed == 0:
                    obj.parent_type = "BONE"
                    obj.parent_bone = "mEyeLeft"
                
                elif eyed == 1:
                    obj.parent_type = "BONE"
                    obj.parent_bone = "mEyeRight"
                
                else:
                    #This should never happen
                    #It only exists as a sanity check
                    raise Exception("Too many eyes!")
                
                #Rotate the eyes to face the front
                obj.rotation_euler.z = math.radians(90)
                
                #Offset the eyes so that they rotate at the bone Head instead of bone Tail
                offset = armature.data.bones[obj.parent_bone].tail \
                 - armature.data.bones[obj.parent_bone].head
                obj.location.y = -offset.x
                
                eyed += 1
            
            #Everything else
            else:
                arm = obj.modifiers.new(type="ARMATURE", name="Armature")
                arm.object = armature
    return added

def register():
    pass

def unregister():
    pass

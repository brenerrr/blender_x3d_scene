
# To run blender without GUI:
#  blender --background --python myscript.py

import bpy
from bpy import data as D
from bpy import context as C
from mathutils import *
from math import *
import numpy as np

solIndexStart = 1777
solIndexFinish = 1777
outPath = '/home/brenerrr/Desktop/'
inpPath = 'outPath'

# Join all objects in objects list of the type objectType
# and name it objectName. Won t merge with protectedObjs
def joinObjects(objects, objectsName, outObjectName, protectedObjs = []):
  # Make sure nothing is selected
  bpy.ops.object.select_all(action='DESELECT')
  # Find mesh objects
  for obj in objects:
    if obj.name.startswith(objectsName) :
      obj.select = True
      bpy.context.scene.objects.active = obj # Activate last selected object

  # Join them
  bpy.ops.object.join()

  # Rename joined objects
  joinedObject = bpy.context.selected_objects[0]
  joinedObject.name = outObjectName

  return joinedObject

# Delete objects in objects list of type objectType or that
# are called objectName. Dont delete objects in protectedObjs list
def deleteObjects(objects, objectName = ' ', protectedObjs = []):
  # Make sure nothing is selected
  bpy.ops.object.select_all(action='DESELECT')
  for obj in objects:
    if obj.name in protectedObjs:
      continue

    elif obj.name.startswith(objectName):
      obj.select = True
      bpy.ops.object.delete()

# Remove materials from objects
def removeMaterialsFromObjects(objects):
  for obj in objects:
    # Set active object
    bpy.context.scene.objects.active = obj
    # Loop through materials and delete them
    for _,_ in enumerate(obj.material_slots.keys()):
      bpy.context.object.active_material_index = 0
      bpy.ops.object.material_slot_remove()

def createMaterialSlot(obj):
  bpy.context.scene.objects.active = obj
  bpy.ops.object.material_slot_add()

def applyMaterial(obj, material):
  if obj.data.materials.keys() == []:
    print('%s doesnt have a material slot... Creating one then!' % obj.name)
    createMaterialSlot(obj)

  obj.data.materials[0] = material


# Setup things that need  to be changed only once
def Setup():
  scene = bpy.context.scene

  bpy.context.scene.render.engine = 'CYCLES' # Cycles render

  # Rendering settings
  scene.cycles.device = 'GPU' # GPU rendering
  scene.render.resolution_x = 1920
  scene.render.resolution_y = 1080
  scene.render.resolution_percentage = 100
  scene.render.use_border = False
  scene.render.resolution_percentage = 100
  scene.cycles.samples = 50
  scene.cycles.transparent_max_bounces = 4
  scene.cycles.transparent_min_bounces = 4
  scene.cycles.max_bounces = 4
  scene.cycles.min_bounces = 4
  scene.cycles.diffusive_bounces = 4
  scene.cycles.glossy_bounces = 4
  scene.cycles.transmission_bounces = 4
  scene.render.tile_x = 256
  scene.render.tile_y = 256

  for obj in scene.objects:
    obj.select = True
    bpy.ops.object.delete()


  # Load materials and objects from blend file
  materialsFile = '/home/brenerrr/hd_main/Blender/airfoil2.blend'
  with bpy.data.libraries.load(materialsFile) as (data_from, data_to):
    data_to.materials = data_from.materials
    # Load cylinder background, camerapth, empty object and empty object path
    data_to.objects = [name for name in data_from.objects if name.lower() in ["cylinder","camerapath","emptyobjectpath","empty","customcamera"] ]

  loadedObjects = {}
  for obj in data_to.objects:
    if obj.name.lower().split('.')[0].startswith('camerapath'): loadedObjects['CameraPath'] = obj
    if obj.name.lower().split('.')[0].startswith('cylinder'): loadedObjects['Cylinder'] = obj
    if obj.name.lower().split('.')[0].startswith('emptyobjectpath'): loadedObjects['EmptyObjectPath'] = obj
    if obj.name.lower().split('.')[0].startswith('empty'): loadedObjects['Empty'] = obj
    if obj.name.lower().split('.')[0].startswith('customcamera'): camera = obj


  # Add lamp
  loc =(-0.3673248291015625, 0.21052122116088867, 2.758418560028076)
  bpy.ops.object.lamp_add(type='HEMI', radius=1, view_align=False, location=loc, layers=(True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False))

  # camera.parent = loadedObjects['CameraPath']
  scene.camera = camera


  return scene, data_to.materials, loadedObjects, camera

def eraseFromMemory(objects, objectName):
  for obj in objects:
    if obj.name.startswith(objectName):
      print(obj.name)
      objects.remove(obj, do_unlink = True)


# ************************************************************************************

scene, materials, loadedObjects, camera = Setup()

data = np.loadtxt('/home/brenerrr/data_2/simulations/3d/second_simulation_plunge/ma_01/postproc/LEPosition.dat')[1:,:]
keys = np.array( [int(x) for x in data[:,1]] )
airfoilOrigin = data[0,0]
cameraOffset = {}
for i, key in enumerate(keys):
  cameraOffset[key] = data[i,0] - airfoilOrigin

_,_,zInitial = scene.camera.location
for material in materials:
  if material.name == 'Qcriterion_Material': qcriterionMaterial = material
  if material.name == 'Surface_Material': surfaceMaterial = material

for obj in loadedObjects.values():
  scene.objects.link(obj)

scene.objects.link(camera)
scene.update()
nFrames = solIndexFinish - solIndexStart + 1
bpy.context.scene.frame_end = nFrames - 1
bpy.context.scene.frame_start = 0
if 'CameraPath' in loadedObjects.keys():
  loadedObjects['CameraPath'].data.path_duration = nFrames
  print (" Camera movement sucessfully imported")

if 'EmptyObjectPath' in loadedObjects.keys():
  loadedObjects['EmptyObjectPath'].data.path_duration = int(0.2 * nFrames)
  print (" Movement of point where the camera is looking sucessfully imported")

for i,solIndex in enumerate(range(solIndexStart,solIndexFinish+1)):
  # Change frame so camera can move
  bpy.context.scene.frame_current = solIndexFinish # XXX
  # i += 1

  deleteObjects(scene.objects,objectName = 'Qcriterion')
  deleteObjects(scene.objects,objectName = 'Surface')

  # Wipe it from memory
  eraseFromMemory(bpy.data.objects, 'Qcriterion')
  eraseFromMemory(bpy.data.objects, 'Surface')
  eraseFromMemory(bpy.data.meshes, 'Shape_Index')

  ## Load qcriterion x3d file
  filepath = '%sqcriterion%d.x3d' % (inpPath,solIndex)
  bpy.ops.import_scene.x3d(filepath=filepath)
  bpy.ops.object.select_all(action='DESELECT')
  # Merge all meshs into a single one
  qcriterion = joinObjects(scene.objects,'Shape_Indexed','Qcriterion',['Cylinder'])

  ## Load surface x3d file
  filepath = '%ssurf%d.x3d' % (inpPath, solIndex)
  bpy.ops.import_scene.x3d(filepath=filepath)
  bpy.ops.object.select_all(action='DESELECT')
  # Merge all meshs into a single one
  surface = joinObjects(scene.objects,'Shape_Indexed','Surface',['Qcriterion','Cylinder'])
  print("\n x3d files loaded")

  # Delete lamps that come with it
  deleteObjects(scene.objects,objectName='DirectLight', protectedObjs='MyLamp')
  eraseFromMemory(bpy.data.lamps, 'Direct')
  print("\n Lamps inputed from files deleted")

  # Delete camera that comes with it
  deleteObjects(scene.objects, objectName='Viewpoint')
  eraseFromMemory(bpy.data.objects, 'Viewpoint')
  print("\n Cameras inputed from files deleted")

  # Add material to surface and qcriterion
  applyMaterial(surface, surfaceMaterial)
  applyMaterial(qcriterion, qcriterionMaterial)
  print ("\n Material added")

  scene.render.filepath='%sframe%s.png' % (outPath,solIndex)
  bpy.ops.render.render(write_still=True)

# # Delete materials from qcriterion and surface
# removeMaterialsFromObjects([surface, qcriterion])
# eraseFromMemory(bpy.data.materials, qcriterionMaterial.name)
# eraseFromMemory(bpy.data.materials, surfaceMaterial.name)
# print( "\n Materials inputed from files deleted")

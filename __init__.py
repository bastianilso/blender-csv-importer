bl_info = {  
 "name": "Import Statistical Data (*.csv)",  
 "author": "Bastian Ilso (bastianilso)",  
 "version": (0, 1),  
 "blender": (2, 7, 7),  
 "location": "File > Import > Import Statistical Data (*.csv)",  
 "description": "Import, visualize and animate data stored as *.csv",  
 "warning": "",  
 "wiki_url": "",  
 "tracker_url": "https://github.com/bastianilso/blender-csv-importer",  
 "category": "Import-Export"}

import bpy
import csv

# Usage: call when you want to print contents of an object
def dump(obj):
   for attr in dir(obj):
       if hasattr( obj, attr ):
           print( "obj.%s = %s" % (attr, getattr(obj, attr)))

def animate_objects(objects, duration):
    print("running animate_objects..")

    # Specify an offset
    offset = 1

    # calculated length of animation per object.    
    animate = duration - (offset * len(objects))
    
    # Store the current frame so we can restore current frame state later.
    startFrame = bpy.context.scene.frame_current
    
    print ("duration in frames: " + str(duration))
    print("amount of objects: " + str(len(objects)))
    print("offset per object: " + str(offset))
    print("animate per object: " + str(animate))

    # Iterate over each data point and animate it.
    for (i, ob) in enumerate(objects):
        print("----")
        print("current frame is: " + str(bpy.context.scene.frame_current))
        print("current offset is: " + str(offset))
        print("current duration is: " + str(animate))
        print("start frame is: " + str(bpy.context.scene.frame_current))
        print("end frame is: " + str(bpy.context.scene.frame_current + animate))
        
        # Insert end keyframe
        bpy.context.scene.frame_current += animate
        ob.keyframe_insert(data_path="location", index=-1)

        # Insert start keyframe
        bpy.context.scene.frame_current -= animate
        ob.location = (ob.location.x,0,0)
        ob.keyframe_insert(data_path="location", index=-1)
        
        # Offset the next object animation
        bpy.context.scene.frame_current += offset

    # Restore frame state    
    bpy.context.scene.frame_current = startFrame


def create_blender_objects(context, columnData, user_object):
    print("create_blender_objects..")

    # Ensure no objects are selected in the scene before proceeding.
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.scene.objects.active = None

    # Create array to store the blender objects
    objects = []
    
    # Iterate over the data and create blender objects for each datapoint.
    # For now we assume the first three columns correspond to X Y Z
    for i in range(len(columnData[0])):
        loc = (columnData[0][i], columnData[1][i], columnData[2][i])
        
        # did the user specify an object? otherwise create placeholder objects.
        if user_object:
            bpy.ops.object.add_named(name=user_object,linked=True)
        else:
            bpy.ops.object.add(radius=0.1)
            
        ob = bpy.context.object
        ob.name="dataPoint" + str(i)
        ob.location=loc
        objects.append(ob)
        
    return objects


def parse_csv(context, filepath):
    print("running parse_csv...")
    f = open(filepath, 'r', encoding='utf-8')
    reader = csv.reader(f, delimiter=',', quotechar='"')
    # TODO: Come up with a way to detect and skip possible headers using this.
    #    dataPoints.__next__()

    # Read the CSV File and store data inside a columns data structure
    columns = []
    for (i, row) in enumerate(reader):
        # Use the length of the first row to determine amount of columns
        if (i == 0):
             columns=[[] for i in range(len(row))]
        # Append values from each parsed row into the array.
        for (j,v) in enumerate(row):
            columns[j].append(float(v))

    # you can access the data using columns[x,y]
    return columns

def update_animate_ui(self, context):
    print("animate boolean was checked!")
    # TODO: Investigate how to do dynamic UI updating here?
    

# ImportHelper is a helper class, defines filename and
# invoke() function which calls the file selector.
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty, IntProperty
from bpy.types import Operator

class ImportCSV(Operator, ImportHelper):
    
    """Imports statistical data (.csv) to visualize as graphs."""
    # Important since its how bpy.ops.import_scene.csv is constructed
    bl_idname = "import_scene.csv"
    bl_label = "Import Statistical Data"

    # ImportHelper mixin class uses this
    filename_ext = ".csv"

    filter_glob = StringProperty(
            default="*.csv",
            options={'HIDDEN'},
            maxlen=255,  # Max internal buffer length, longer would be clamped.
            )

    # List of operator properties, the attributes will be assigned
    # to the class instance from the operator settings before calling.
    use_animate = BoolProperty(
            name="Animate",
            description="Animate the data",
            default=True,
            update=update_animate_ui
            )
          
    set_duration = IntProperty(
            name="Duration",
            description="Duration of the animation (in frames)",
            default=17,
            subtype="TIME",
            )
                    
    type = EnumProperty(
            name="Visualization Type",
            description="Choose between two items",
            items=(('OPT_A', "Scatter Plot", "Position each datapoint in X, Y, Z"),
                   ('OPT_B', "Second Option", "Description two")),
            default='OPT_A',
            )
            
    set_object = StringProperty(
            name="Object",
            description="Choose an object to represent each data point (Optional).",
            )

    def execute(self, context):
        dataColumns = parse_csv(context, self.filepath)
        objects = create_blender_objects(context, dataColumns, self.set_object)
        if (self.use_animate):
            animate_objects(objects, self.set_duration)
        return {'FINISHED'}
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene

        box = layout.box()
        box.prop(self, 'type')
        box.prop_search(self, "set_object", scene, "objects",text="Object")
        box.prop(self, 'use_animate')
        if (self.use_animate):
            box.prop(self, 'set_duration')
        

def menu_func_import(self, context):
    self.layout.operator(ImportCSV.bl_idname, text="Statistical Data (.csv)")


def register():
    bpy.utils.register_class(ImportCSV)
    bpy.types.INFO_MT_file_import.append(menu_func_import)

def unregister():
    bpy.utils.unregister_class(ImportCSV)
    bpy.types.INFO_MT_file_import.remove(menu_func_import)


if __name__ == "__main__":
    register()

    # test call
    #bpy.ops.import_scene.csv('INVOKE_DEFAULT')


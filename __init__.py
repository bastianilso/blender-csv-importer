# <pep8 compliant>
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

# Usage: call when you want to print contents of an object
def dump(obj):
   for attr in dir(obj):
       if hasattr( obj, attr ):
           print( "obj.%s = %s" % (attr, getattr(obj, attr)))

import bpy
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty, IntProperty, PointerProperty
from bpy.types import Operator, PropertyGroup
import csv

redraw = 0

class DataStorage():
    
    data = None

    def __init__(self, d = None):
        self.data = d
    
    def add_row(self, row):        
        # TODO: zero-pad all entries if the length of a row exceeds already added rows.
        # Use the length of the first row to determine amount of columns
        if (self.data == None):
            self.data = []
            self.data = [[] for i in range(len(row))]

        # Append values from each parsed row into the array.
        for (j,v) in enumerate(row):
            self.data[j].append(float(v))
            print(v)
    
    def get_columns(self):
        return self.data
    
    #def get_rows(self):
        # define a new dataset which is an array of rows.
        # 
        
# TODO: Define toString method

# TODO: Make Abstract Visualizer Class.

class HistogramVisualizer():

    dataStore = None
    bl_objects = None
    props = None

    def visualize(self, dataStorage):
        print("visualize!")
    
    def draw(self, layout, context):
        print("bla!")

class PieVisualizer():

    dataStore = None
    bl_objects = None
    props = None

    def create_blender_objects(self):
        # Ensure no objects are selected in the scene before proceeding.
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.scene.objects.active = None
        
        objects = []
        
        # Calculate how many segments to have on the primitive.
        # Create a circle Primitive with X segments
        
        
        for i in range(len(data[0])):
            loc = (data[0][i], data[1][i], data[2][i])
        

    def visualize(self, dataStorage):
        print("visualize!")
        
    def draw(self, layout, context):
        print("bla!")

class ScatterVisualizer(): 
    
    dataStore = None
    bl_objects = None
    props = None

    def visualize(self, dataStorage):
        self.dataStore = dataStorage
        self.props = bpy.context.scene.import_csv.visprops
        self.create_blender_objects()
        if (self.props.use_animate):
            self.animate_objects()
        
    def create_blender_objects(self):
        print("create_blender_objects..")

        # Ensure no objects are selected in the scene before proceeding.
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.scene.objects.active = None

        data = self.dataStore.get_columns()

        # Create array to store the blender objects
        objects = []
        
        # Iterate over the data and create blender objects for each datapoint.
        # For now we assume the first three columns correspond to X Y Z
        for i in range(len(data[0])):
            loc = (data[0][i], data[1][i], data[2][i])
            
            # did the user specify an object? otherwise create placeholder objects.
            if self.props.point_object:
                bpy.ops.object.add_named(name=self.props.point_object,linked=True)
            else:
                bpy.ops.object.add(radius=0.1)
                
            ob = bpy.context.object
            ob.name="dataPoint" + str(i)
            ob.location=loc
            objects.append(ob)
            
        self.bl_objects = objects
    
    def animate_objects(self):
        print("running animate_objects..")
        
        duration = self.props.duration
        objects = self.bl_objects
        
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

    def draw(self, layout, context):
        layout.label("test")
        box = layout.box()
        props = context.scene.import_csv.visprops
        scene = context.scene

        box.prop_search(props, "point_object", scene, "objects",text="Object")
        # TODO: Expose how things should be mapped also
        box.prop(props, 'use_animate')
        if (props.use_animate):
            box.prop(props, 'duration')
            # TODO: Expose Animation Type    
    
class CSVReader():

    filepath = None
    delimiter = ','
    quotechar = '"'
    __headers = None

    def __init__(self, f):
        self.filepath = f
        # detect delimiter
        # detect quotechar
        # detect_labels

    def __detect_delimiter(self):
        self.delimiter = ','
        # does the file contain tabs? then return a string with 'TAB'
        # otherwise, assume delimiter is comma

    def __detect_quotechar(self):
        self.quotechar = '"'
        # detect quotechar based on frequency of either ' or "
        # if none, then fallback to " (it wouldnt matter then)

    def __detect_labels(self):
        self.__headers = None
        # does the file contain numerical data?
            #no, then expose manual boolean for detecting labels.
        # is the first line strings or numerical data?
            # if it is strings, then assume it is labels. 

    def parse_csv(self, context, filepath):
        print("running parse_csv...")
        f = open(filepath, 'r', encoding='utf-8')
        reader = csv.reader(f, delimiter=',', quotechar='"')
        # TODO: Come up with a way to detect and skip possible headers using this.
        #if (headers):
            #reader.__next__()

        # Read the CSV File and store data inside a columns data structure
        columns = []
        dataStore = DataStorage()
        for (i, row) in enumerate(reader):
            dataStore.add_row(row)

        # you can access the data using dataStore.get_rows()[x,y]
        return dataStore

class VisualizationProperties(PropertyGroup):
    duration = IntProperty(
            name="Duration",
            description="Duration of the animation (in frames)",
            default=17,
            subtype="TIME",
            )
            
    point_object = StringProperty(
            name="Object",
            description="Choose an object to represent each data point (Optional).",
            )
            
    use_animate = BoolProperty(
            name="Animate",
            description="Animate the data",
            default=True,
            )
                        
    my_float1 = bpy.props.FloatProperty()

class ImportCSVProperties(PropertyGroup):
    visprops = bpy.props.PointerProperty(type=VisualizationProperties)

    def update_visualizer (other, context):
        # We change visualizer using an index because
        # changing the visualizer itself is not possible from here
        # since objects and string are immutable in python.
        props = bpy.context.scene.import_csv
        if (other.type == 'OPT_SCATTER'):
            props.vis_index = 0
        elif (other.type == 'OPT_PIE'):
            props.vis_index = 1
        elif (other.type == 'OPT_HIST'):
            props.vis_index = 2
        return None
        
    type = EnumProperty(
            name="Type",
            description="Choose Visualization Type",
            items=(('OPT_SCATTER', "Scatter Plot", "Position each datapoint in X, Y, Z"),
                   ('OPT_PIE', "Pie Chart", "Description two"),
                   ('OPT_HIST', "Histogram", "Description two")),
            default='OPT_SCATTER',
            update=update_visualizer
            )
    visualizers = [ScatterVisualizer(), PieVisualizer(), HistogramVisualizer()]
    vis_index = bpy.props.IntProperty()


# ImportHelper is a helper class, defines filename and
# invoke() function which calls the file selector.

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
        
    def execute(self, context):   
        reader = CSVReader(self.filepath)
        dataStore = reader.parse_csv(context, self.filepath)
        
        current = context.scene.import_csv.vis_index
        visualizer = context.scene.import_csv.visualizers[current]
        visualizer.visualize(dataStore)
        return {'FINISHED'}
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.import_csv

        box = layout.box()
        box.prop(props, 'type')
        if (props.visualizers):
            props.visualizers[props.vis_index].draw(layout, context)
        

def menu_func_import(self, context):    
    self.layout.operator(ImportCSV.bl_idname, text="Statistical Data (.csv)")

classes = (
    VisualizationProperties,
    ImportCSVProperties,
    ImportCSV
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.import_csv = PointerProperty(type=ImportCSVProperties)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Operator.import_csv
    
    bpy.types.INFO_MT_file_import.remove(menu_func_import)

if __name__ == "__main__":
    register()
    
    # test call
    bpy.ops.import_scene.csv('INVOKE_DEFAULT')



import bpy 

print("Hello World")
print(bpy.data.objects) # print an array with all objects in the scene
print(bpy.data.objects[0].location) # print a vector containing the location of the first object in the scene


# usually you work with data currently in the context, fx selected objects etc.
print(bpy.context.active_object) #prints the currently selected object
bpy.context.active_object.location[0] = 1 # set location of active object to '1'

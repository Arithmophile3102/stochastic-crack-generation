import adsk.core, adsk.fusion, traceback, random # type: ignore

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        design = adsk.fusion.Design.cast(app.activeProduct)

        # create a new plate
        plate = create_plate(design.rootComponent, app, design, ui)
        ui.messageBox(f"Plate ({plate.name}) created successfully!")

        # put a crack in the plate
        # create_crack(plate, design.rootComponent, app, ui, design)
        # ui.messageBox("Stochastic crack created successfully!")

    except Exception as e:
        if ui:
            ui.messageBox("Error: {}".format(str(e)))
        traceback.print_exc()

def create_plate(root_component, app, design, ui):
    try:
        # helpful lists
        planes = root_component.constructionPlanes
        sketches = root_component.sketches
        extrudes = root_component.features.extrudeFeatures

        # ================== CREATING A PLANE ==================
        target_axis = root_component.xConstructionAxis
        target_angle = adsk.core.ValueInput.createByReal(0.0)
        reference_plane = root_component.xYConstructionPlane

        plane_input = planes.createInput()
        plane_input.setByAngle(target_axis, target_angle, reference_plane)
        
        plane = planes.add(plane_input)

        # ================== CREATING A SKETCH ==================
        sketch = sketches.add(plane)
        sketch.name = "plane_sketch"

        # ================== CREATING A RECTANGLE ==================
        width = 20
        height = 20

        center_point = adsk.core.Point3D.create(0, 0, 0)
        corner_point = adsk.core.Point3D.create(width/2, height/2, 0)

        # add points to rectangle geometry
        rectangle_lines = sketch.sketchCurves.sketchLines.addCenterPointRectangle(center_point, corner_point)

        # ================== EXTRUDING A PLATE ==================
        profile_collection = adsk.core.ObjectCollection.create()
        for p in sketch.profiles:
            profile_collection.add(p)
        
        distance_input = adsk.core.ValueInput.createByString("1 mm")
        distance_extent = adsk.fusion.DistanceExtentDefinition.create(distance_input)

        extrude_input = extrudes.createInput(
            profile_collection,
            adsk.fusion.FeatureOperations.NewBodyFeatureOperation
        )

        extrude_input.setOneSideExtent(distance_extent, adsk.fusion.ExtentDirections.PositiveExtentDirection)
        extrude_input.isSolid = True

        extrude_feature = extrudes.add(extrude_input)

        # ================== NAMING THE BODY ==================
        body = extrude_feature.bodies.item(0)
        body.name = "plate"

        # ================== MATERIAL ASSIGNMENT ==================
        
        # check if material exists
        material = design.materials.itemByName("Aluminum 6061")
        
        # apply material or send message
        if material:
            body.material = material
        else:
            ui.messageBox("WARNING: Aluminum 6061 material was not located, so the operation will continue with the default material.")

        return body


    except Exception as e:
        traceback.print_exc()
        raise e

def create_crack(plate, root_component, app, ui, design):
    try:
        # helpful lists
        planes = root_component.constructionPlanes
        sketches = root_component.sketches
        extrudes = root_component.features.extrudeFeatures

        # find correct face
        faces = plate.faces
        correct_face = plate.faces.item(4)

        # create new sketch on that face
        sketch = sketches.add(correct_face)
        sketch_points = sketch.sketchPoints
        sketch_lines = sketch.sketchCurves.sketchLines
        sketch.name = "crack_sketch"

        # add central point to that sketch for the crack
        central_x = random.uniform(-10, 10)
        central_y = random.uniform(-10, 10)
        central_point_coordinates = adsk.core.Point3D.create(central_x, central_y, 0)
        central_point = sketch_points.add(central_point_coordinates)

        # notify users of central point coordinates
        ui.messageBox(f"Central point created at: ({central_x}, {central_y})")

        # generate secondary points for the crack
        number_of_secondary_points = random.randint(3, 6)
        range_of_secondary_points = random.gauss(0, 2)
        secondary_points = []
        for i in range(number_of_secondary_points):
            secondary_x = random.uniform(central_x - range_of_secondary_points, central_x + range_of_secondary_points)
            secondary_y = random.uniform(central_y - range_of_secondary_points, central_y + range_of_secondary_points)
            secondary_point_coordinates = adsk.core.Point3D.create(secondary_x, secondary_y, 0)
            secondary_point = sketch_points.add(secondary_point_coordinates)
            secondary_points.append(secondary_point)

        # connect secondary points to the central point
        for point in secondary_points:
            line = sketch_lines.addByTwoPoints(central_point, point)

    
    except Exception as e:
        traceback.print_exc()
        raise e
import adsk.core, adsk.fusion, traceback, random, math # type: ignore

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
        create_crack(plate, design.rootComponent, app, ui, design)
        ui.messageBox("Stochastic crack created successfully!")

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

        # define the relative central point of the crack

        central_relative = [0, 0]

        # next, the random crack growth angles will be determined.

        first_growth_angle = random.uniform(0, 360)
        second_growth_angle = (first_growth_angle + 180) % 360

        growth_length = round(random.normalvariate(10, 2.5))

        # branch 1 bends left
        first_growth_segments = get_growth_segments(first_growth_angle, growth_length, bend_bias=0)

        # branch 2 bends right
        second_growth_segments = get_growth_segments(second_growth_angle, growth_length, bend_bias=0)


        grow_crack(central_relative, first_growth_segments, second_growth_segments, sketch_points, sketch_lines)

    
    except Exception as e:
        traceback.print_exc()
        raise e

def get_growth_segments(base_heading_deg, length, bend_bias):
    # convert base heading to radians
    base_heading = math.radians(base_heading_deg)

    # starting point
    starting_point = [0, 0]

    # cumulative bend (keeps cracks separated)
    cumulative_bend = 0

    segments = []

    for _ in range(length):
        # segment length
        segment_length = abs(random.normalvariate(0.1, 0.05))

        # add biased bending
        cumulative_bend += math.radians(random.normalvariate(bend_bias, 20))

        # final angle = base heading + cumulative bend
        segment_angle = base_heading + cumulative_bend

        # compute endpoint
        x = starting_point[0] + segment_length * math.cos(segment_angle)
        y = starting_point[1] + segment_length * math.sin(segment_angle)
        endpoint = [x, y]

        segments.append([starting_point.copy(), endpoint])

        starting_point = endpoint

    return segments

def grow_crack(central_relative, first_growth_segments, second_growth_segments, sketch_points, sketch_lines):
    # find out how large the crack window is
    largest_x = 0
    largest_y = 0
    lowest_x = 0
    lowest_y = 0

    all_segments = first_growth_segments + second_growth_segments
    for segment in all_segments:

        x1 = segment[0][0]
        y1 = segment[0][1]
        x2 = segment[1][0]
        y2 = segment[1][1]

        if x1 > largest_x:
            largest_x = x1
        if x2 > largest_x:
            largest_x = x2
        if y1 > largest_y:
            largest_y = y1
        if y2 > largest_y:
            largest_y = y2

        if x1 < lowest_x:
            lowest_x = x1
        if x2 < lowest_x:
            lowest_x = x2
        if y1 < lowest_y:
            lowest_y = y1
        if y2 < lowest_y:
            lowest_y = y2
        
    difference_x = largest_x - lowest_x
    difference_y = largest_y - lowest_y

    # place crack window by top left corner
    range_x = 20 - difference_x
    range_y = 20 - difference_y

    offset_x = random.uniform(-10, 10 - difference_x)
    offset_y = random.uniform(-10, 10 - difference_y)

    # apply offsets
    for segment in all_segments:
        segment[0][0] += offset_x
        segment[0][1] += offset_y
        segment[1][0] += offset_x
        segment[1][1] += offset_y
    central_absolute = [central_relative[0] + offset_x, central_relative[1] + offset_y]

    # create points for the crack
    central_point_coordinates = adsk.core.Point3D.create(central_absolute[0], central_absolute[1], 0)
    central_point = sketch_points.add(central_point_coordinates)
    # draw first growth
    previous_coordinates = adsk.core.Point3D.create(central_absolute[0], central_absolute[1], 0)
    previous = sketch_points.add(previous_coordinates)

    for segment in first_growth_segments:
        # translated start point
        start_coordinates = adsk.core.Point3D.create(segment[0][0], segment[0][1], 0)
        start_point = sketch_points.add(start_coordinates)

        # translated end point
        end_coordinates = adsk.core.Point3D.create(segment[1][0], segment[1][1], 0)
        end_point = sketch_points.add(end_coordinates)

        # draw segment
        sketch_lines.addByTwoPoints(start_point, end_point)

    # draw second growth
    previous_coordinates = adsk.core.Point3D.create(central_absolute[0], central_absolute[1], 0)
    previous = sketch_points.add(previous_coordinates)

    for segment in second_growth_segments:
        start_coordinates = adsk.core.Point3D.create(segment[0][0], segment[0][1], 0)
        start_point = sketch_points.add(start_coordinates)

        end_coordinates = adsk.core.Point3D.create(segment[1][0], segment[1][1], 0)
        end_point = sketch_points.add(end_coordinates)

        sketch_lines.addByTwoPoints(start_point, end_point)
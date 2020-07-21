# Copyright (C) 2020

format_spec = {
    "name": "DDLN_CSV",
    "dumpers": [
        {
            "display_name": "{name} {format} {version} for images (BB)",
            "format": "ZIP",
            "version": "0.1",
            "handler": "dump_ddln_csv"
        }
    ],
    "loaders": [
        {
            "display_name": "{name} {format} {version}",
            "format": "CSV",
            "version": "0.1",
            "handler": "load",
        }
    ],
}

def extractFileParams(filename):
    directoryName = filename.split("/")[2]
    csvFilename = filename.split("/")[-1]
    csvFilename = csvFilename[:-4] + "_y_bb.csv"
	
    return directoryName,csvFilename

def writeToCsv(dirname, filename, data):
    try:
        if not os.path.exists(dirname):
            os.mkdir(dirname)
        with open(dirname + filename, 'w', newline='') as csvfile:
            csvfile.write(data)            
    except Exception as e:
        return e  #for debugging
            
    return True

def dump_ddln_csv(file_object, annotations):
    from cvat.apps.dataset_manager.util import make_zip_archive
    from tempfile import TemporaryDirectory

    with TemporaryDirectory() as temp_dir:
        log_file_path = temp_dir + "/" + "export.log"
        log_data = ""; 
        totalSucceed = 0; totalFailed = 0; boxIndex = 0

        with open(log_file_path, 'w', newline='') as log_file:
            for frame_annotation in annotations.group_by_frame(omit_empty_frames=False):
                image_name = frame_annotation.name
                image_width = frame_annotation.width
                image_height = frame_annotation.height
                
                log_data = log_data + "Image: {}\n".format(image_name)
                csv_data = ""

                for shape in frame_annotation.labeled_shapes:
                    boxIndex += 1

                    label = shape.label
                    xtl = shape.points[0]
                    ytl = shape.points[1]
                    xbr = shape.points[2]
                    ybr = shape.points[3]

                    normalizedXtl = "{:.6f}".format(float(xtl) / float(image_width))
                    normalizedYtl = "{:.6f}".format(float(ytl) / float(image_height))
                    normalizedXbr = "{:.6f}".format(float(xbr) / float(image_width))
                    normalizedYbr = "{:.6f}".format(float(ybr) / float(image_height))
                    
                    classid = -99; trackid = -99
                    for attr in shape.attributes:
                        if attr.name == "Object_class":
                            classid = attr.value
                        if attr.name == "Track_id":
                            trackid = attr.value

                    log_line = "Initial data: {} | {},{},{},{},{},{} | {}\n".format(label, xtl, ytl, xbr, ybr, classid, trackid, shape.attributes)
                    log_data = log_data + log_line
                    
                    csv_line = "{},{},{},{},{},{}\n".format(normalizedXtl, normalizedYtl, normalizedXbr, normalizedYbr, classid, trackid)
                    csv_data = csv_data + csv_line
                    log_line = "Converted data: {}".format(csv_line)
                    log_data = log_data + log_line
                        
                dir_name, csv_file_name  = extractFileParams(image_name)
                dir_name = temp_dir + "/" + dir_name + "/"
                log_line = "Dir: {}; File: {}\n".format(dir_name, csv_file_name)
                log_data = log_data + log_line

                log_line = "Added to [{}] ..\n".format(csv_file_name)
                log_data = log_data + log_line

                write_result = writeToCsv(dir_name, csv_file_name, csv_data)
                if write_result == True:
                    totalSucceed += 1
                else:
                    log_data = log_data + str(write_result) + "\n" 
                    totalFailed += 1
                
            log_data = log_data + "\n"       
            log_data = log_data + "Successfully created files: {}\n".format(totalSucceed)
            log_data = log_data + "Failed: {}\n".format(totalFailed)
            log_data = log_data + "Total: {}\n".format(totalSucceed+totalFailed)
            log_data = log_data + "Boxes: {}\n".format(boxIndex)
            log_file.write(log_data)
        
        make_zip_archive(temp_dir, file_object)

def load(file_object, annotations):
    from cvat.apps.annotation.ddln_zip_importer import (
        build_frame_id_mapping,
        CsvZipImporter,
        add_bbox,
    )

    frame_id_by_names = build_frame_id_mapping(annotations)

    importer = CsvZipImporter(file_object)
    for frame_reader in importer.iterate_frames():
        frame_id = frame_id_by_names[frame_reader.name, frame_reader.sequence_name]
        for bbox in frame_reader.iterate_bboxes():
            add_bbox(bbox, frame_id, annotations)

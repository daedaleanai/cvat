# Copyright (C) 2020

format_spec = {
    "name": "DDLN_CSV_BB",
    "dumpers": [
        {
            "display_name": "{name} {format} {version} for images [BB]",
            "format": "ZIP",
            "version": "0.9",
            "handler": "dump"
        }
    ],
    "loaders": [
        {
            "display_name": "{name} {format} {version} for images [BB]",
            "format": "ZIP",
            "version": "0.9",
            "handler": "load",
        }
    ],
}

def extractFileParams(filename):
    directoryName, csvFilename = os.path.split(filename)
    if directoryName:
        directoryName = directoryName.split("/")[2]
    # for local testing
    else:
        directoryName = "dummy"
    csvFilename = os.path.splitext(csvFilename)[0] + "_y.csv"

    return directoryName,csvFilename

def writeToCsv(dirname, filename, data):
    try:
        if not os.path.exists(dirname):
            os.mkdir(dirname)
        with open(os.path.join(dirname, filename), 'w', newline='') as csvfile:
            csvfile.write(data)
    except Exception as e:
        print("Error saving {}: {}".format(filename, e))
        return False

    return True

def dump(file_object, annotations):
    from cvat.apps.dataset_manager.util import make_zip_archive
    from cvat.apps.annotation.structures import load_sequences
    from cvat.apps.annotation.transports.csv import CsvDirectoryImporter
    from cvat.apps.engine.ddln.utils import write_task_mapping_file, write_ddln_yaml_file, guess_task_name
    from cvat.apps.annotation.validation import validate
    from tempfile import TemporaryDirectory

    task_name = guess_task_name(annotations.meta['task']['name'])

    with TemporaryDirectory() as temp_dir:
        log_file_path = os.path.join(temp_dir, "export.log")
        yml_file_path = os.path.join(temp_dir, "ddln.yaml")
        totalSucceed = 0
        totalFailed = 0
        boxIndex = 0

        with open(yml_file_path, 'w', newline='') as yml_file:
            write_ddln_yaml_file(task_name, yml_file, {})

        with open(log_file_path, 'w', newline='') as log_file:
            for frame_annotation in annotations.group_by_frame(omit_empty_frames=False):
                image_name = frame_annotation.name
                image_width = frame_annotation.width
                image_height = frame_annotation.height

                log_file.write("Image: {}\n".format(image_name))
                csv_data = ""

                for index, shape in enumerate(frame_annotation.labeled_shapes, 1):
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

                    classid = -99
                    trackid = -99
                    for attr in shape.attributes:
                        if attr.name == "Object_class":
                            classid = attr.value
                        if attr.name == "Track_id":
                            trackid = attr.value

                    log_file.write("Initial data: [{}] {} | {},{},{},{},{},{} | {}\n".format(
                            index, label, xtl, ytl, xbr, ybr, classid, trackid, shape.attributes))

                    csv_line = "{},{},{},{},{},{}\n".format(normalizedXtl, normalizedYtl, normalizedXbr, normalizedYbr, classid, trackid)
                    csv_data = csv_data + csv_line
                    log_file.write("Converted data: {}".format(csv_line))

                dir_name, csv_file_name  = extractFileParams(image_name)
                dir_name = os.path.join(temp_dir, dir_name)
                log_file.write("Dir: {}; Added to file: {}\n".format(dir_name, csv_file_name))

                write_result = writeToCsv(dir_name, csv_file_name, csv_data)

                if write_result == True:
                    totalSucceed += 1
                else:
                    totalFailed += 1

            log_file.write("\nSuccessfully created files: {}\n".format(totalSucceed))
            log_file.write("Failed: {}\n".format(totalFailed))
            log_file.write("Total: {}\n".format(totalSucceed+totalFailed))
            log_file.write("Boxes: {}\n".format(boxIndex))

        sequences = load_sequences(CsvDirectoryImporter(temp_dir))
        reporter = validate(sequences)
        validation_file = os.path.join(temp_dir, 'validation.txt')
        reporter.write_text_report(open(validation_file, 'wt'))
        task_mapping_filename = os.path.join(temp_dir, 'task_mapping.csv')
        write_task_mapping_file(annotations._db_task, open(task_mapping_filename, 'wt'))
        make_zip_archive(temp_dir, file_object)


def load(file_object, annotations):
    from cvat.apps.annotation.transports.csv import CsvZipImporter
    from cvat.apps.annotation.transports.cvat import CVATExporter

    importer = CsvZipImporter(file_object)
    with CVATExporter(annotations) as exporter:
        for frame_reader in importer.iterate_frames():
            with exporter.begin_frame(frame_reader.name, frame_reader.sequence_name) as frame_writer:
                for bbox in frame_reader.iterate_bboxes():
                    frame_writer.write_bbox(bbox)

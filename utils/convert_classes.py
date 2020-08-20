import json

json_path = "20200811_wooden.json"


def to_pts(region):
    x = region['shape_attributes']['all_points_x']
    y = region['shape_attributes']['all_points_y']
    xy = zip(x, y)
    xy.sort()
    pts = {}

    if xy[0][1] < xy[1][1]:
        pts['00'], pts['01'] = (xy[0][0], xy[0][1]), (xy[1][0], xy[1][1])
    else:
        pts['00'], pts['01'] = (xy[1][0], xy[1][1]), (xy[0][0], xy[0][1])

    if xy[2][1] < xy[3][1]:
        pts['10'], pts['11'] = (xy[2][0], xy[2][1]), (xy[3][0], xy[3][1])
    else:
        pts['10'], pts['11'] = (xy[3][0], xy[3][1]), (xy[2][0], xy[2][1])

    return pts


def convert_class(regions):
    converted = {}
    # print(regions)
    if 'left_hole' in regions and 'face' in regions:
        # left_side
        box = {}
        box['00'], box['01'] = regions['face']['00'], regions['face']['01']
        box['10'], box['11'] = regions['left_hole']['00'], regions['left_hole']['01']
        converted['left_side'] = box
    if 'right_hole' in regions and 'face' in regions:
        # right_side
        box = {}
        box['00'], box['01'] = regions['right_hole']['10'], regions['right_hole']['11']
        box['10'], box['11'] = regions['face']['10'], regions['face']['11']
        converted['right_side'] = box
    if 'left_hole' in regions and 'right_hole' in regions:
        # center
        box = {}
        box['00'], box['01'] = regions['left_hole']['10'], regions['left_hole']['11']
        box['10'], box['11'] = regions['right_hole']['00'], regions['right_hole']['01']
        converted['center'] = box
    if 'face' in regions:
        # right_side
        box = {}
        box['00'], box['01'] = regions['face']['00'], regions['face']['01']
        box['10'], box['11'] = regions['face']['10'], regions['face']['11']
        converted['face'] = box

    return converted


def to_annotation_format(pts):
    regions = []
    for key in pts:
        shape = {}
        shape[u'all_points_x'] = [pts[key][p][0] for p in ['00', '01', '11', '10']]
        shape[u'all_points_y'] = [pts[key][p][1] for p in ['00', '01', '11', '10']]
        shape[u'name'] = 'polygon'

        region = {}
        region[u'shape_attributes'] = shape
        region[u'region_attributes'] = {u'type': key}
        regions.append(region)

    return regions

def update_regions(regions):
    # print(regions)
    # print("--------------------------------------------------------")
    if len(regions) == 0 or len(regions) > 3:
        return []

    # find duplicate
    pts = {}
    for r in regions:
        key = r['region_attributes']['type']
        if key in pts:
            # Duplicate type
            return []

        if len(r['shape_attributes']['all_points_x']) != 4:
            # Cannot handle this case
            return []

        pts[key] = to_pts(r)

    converted_pts = convert_class(pts)

    converted_regions = to_annotation_format(converted_pts)
    # print(converted_regions)

    return converted_regions

if __name__ == "__main__":
    # Open input json
    f = open(json_path, 'r')
    dat = json.load(f)
    f.close()

    # print(dat.keys())
    # [u'_via_attributes',
    #  u'_via_img_metadata',
    #  u'_via_image_id_list',
    #  u'_via_settings',
    #  u'_via_data_format_version']

    # Update '_via_attributes'
    print("old", dat['_via_attributes']['region']['type']['options'])
    # dat[u'_via_attributes'][u'region'][u'type'][u'default_options'] = {u'center': True}
    dat[u'_via_attributes'][u'region'][u'type'][u'options'] = \
            {u'left_side': u'', u'right_side': u'', u'center': u'', u'face': u''}
    print("new", dat['_via_attributes']['region']['type']['options'])

    for img in dat[u'_via_img_metadata']:
        # [u'regions', u'size', u'file_attributes', u'filename']
        new_regions = update_regions(dat['_via_img_metadata'][img]['regions'])
        if len(dat['_via_img_metadata'][img]['regions']) != 0 and \
                len(new_regions) != len(dat['_via_img_metadata'][img]['regions']) + 1:
            print("Regions decreased: {}".format(img))
        dat[u'_via_img_metadata'][img][u'regions'] = new_regions

    f = open(json_path.replace('.json', '_frame.json'), 'w')
    json.dump(dat, f)
    f.close()

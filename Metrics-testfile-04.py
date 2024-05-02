def delete_cluster(
    project_id: str, zone: str, private_cloud_name: str, cluster_name: str
) -> operation.Operation:
    client = vmwareengine_v1.VmwareEngineClient()
    request = vmwareengine_v1.DeleteClusterRequest()
    request.name = (
        f"projects/{project_id}/locations/{zone}/privateClouds/{private_cloud_name}"
        f"/clusters/{cluster_name}"
    )
    return client.delete_cluster(request)


def delete_legacy_network(project_id: str, region: str) -> operation.Operation:
    client = vmwareengine_v1.VmwareEngineClient()
    return client.delete_vmware_engine_network(
        name=f"projects/{project_id}/"
        f"locations/{region}/"
        f"vmwareEngineNetworks/{region}-default"
    )

def get_operation_by_name(operation_name: str) -> Operation:
    client = vmwareengine_v1.VmwareEngineClient()
    request = GetOperationRequest()
    request.name = operation_name
    return client.get_operation(request)


def list_locations(project_id: str) -> str:
    client = vmwareengine_v1.VmwareEngineClient()
    request = ListLocationsRequest()
    request.name = f"projects/{project_id}"
    locations = client.list_locations(request)
    print(locations)
    return str(locations)


def get_crop_hint(path: str) -> MutableSequence[vision.Vertex]:
    # [START vision_crop_hints_tutorial_get_crop_hints]
   
    client = vision.ImageAnnotatorClient()

    with open(path, "rb") as image_file:
        content = image_file.read()

    image = vision.Image(content=content)

    crop_hints_params = vision.CropHintsParams(aspect_ratios=[1.77])
    image_context = vision.ImageContext(crop_hints_params=crop_hints_params)

    response = client.crop_hints(image=image, image_context=image_context)
    hints = response.crop_hints_annotation.crop_hints

    # Get bounds for the first crop hint using an aspect ratio of 1.77.
    vertices = hints[0].bounding_poly.vertices
    # [END vision_crop_hints_tutorial_get_crop_hints]

    return vertices


def draw_hint(image_file: str) -> None:
    # [START vision_crop_hints_tutorial_draw_crop_hints]
    vects = get_crop_hint(image_file)

    im = Image.open(image_file)
    draw = ImageDraw.Draw(im)
    draw.polygon(
        [
            vects[0].x,
            vects[0].y,
            vects[1].x,
            vects[1].y,
            vects[2].x,
            vects[2].y,
            vects[3].x,
            vects[3].y,
        ],
        None,
        "red",
    )
    im.save("output-hint.jpg", "JPEG")
    print("Saved new image to output-hint.jpg")
    # [END vision_crop_hints_tutorial_draw_crop_hints]"


def crop_to_hint(image_file: str) -> None:
     # [START vision_crop_hints_tutorial_crop_to_hints]
    vects = get_crop_hint(image_file)

    im = Image.open(image_file)
    im2 = im.crop([vects[0].x, vects[0].y, vects[2].x - 1, vects[2].y - 1])
    im2.save("output-crop.jpg", "JPEG")
    print("Saved new image to output-crop.jpg")


def create_live_session(
    project_id: str, location: str, live_config_id: str
) -> stitcher_v1.types.LiveSession:

    client = VideoStitcherServiceClient()

    parent = f"projects/{project_id}/locations/{location}"
    live_config = (
        f"projects/{project_id}/locations/{location}/liveConfigs/{live_config_id}"
    )

    live_session = stitcher_v1.types.LiveSession(live_config=live_config)

    response = client.create_live_session(parent=parent, live_session=live_session)
    print(f"Live session: {response.name}")
    return response


def get_live_ad_tag_detail(
    project_id: str, location: str, session_id: str, ad_tag_detail_id: str
) -> stitcher_v1.types.LiveAdTagDetail:

    client = VideoStitcherServiceClient()

    name = client.live_ad_tag_detail_path(
        project_id, location, session_id, ad_tag_detail_id
    )
    response = client.get_live_ad_tag_detail(name=name)
    print(f"Live ad tag detail: {response.name}")
    return response

def get_vod_ad_tag_detail(
    project_id: str, location: str, session_id: str, ad_tag_detail_id: str
) -> stitcher_v1.types.VodAdTagDetail:
  
    client = VideoStitcherServiceClient()

    name = client.vod_ad_tag_detail_path(
        project_id, location, session_id, ad_tag_detail_id
    )
    response = client.get_vod_ad_tag_detail(name=name)
    print(f"VOD ad tag detail: {response.name}")
    return response

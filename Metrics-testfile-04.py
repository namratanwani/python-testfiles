def delete_cluster(
    project_id: str, zone: str, private_cloud_name: str, cluster_name: str
) -> operation.Operation:
    """
    Deletes a cluster from VMware Engine by specifying its name, project ID, zone,
    and private cloud name.

    Args:
        project_id (str): identifier of the project for which a private cloud is
            located.
        zone (str): zone where the private cloud is located, which is used to
            identify the private cloud in the deletion operation.
        private_cloud_name (str): name of the private cloud where the cluster to
            be deleted is located.
        cluster_name (str): name of the cluster to be deleted.

    Returns:
        operation.Operation: an `operation.Operation` object representing the
        result of the cluster deletion operation.

    """
    client = vmwareengine_v1.VmwareEngineClient()
    request = vmwareengine_v1.DeleteClusterRequest()
    request.name = (
        f"projects/{project_id}/locations/{zone}/privateClouds/{private_cloud_name}"
        f"/clusters/{cluster_name}"
    )
    return client.delete_cluster(request)


def delete_legacy_network(project_id: str, region: str) -> operation.Operation:
    """
    Deletes a VMware engine network in a specified region and project.

    Args:
        project_id (str): identifier of a specific project to which the legacy
            network belongs, which is used as a part of the path for the delete operation.
        region (str): location of the network to be deleted within the specified
            project, and is used as part of the delete call in the client method.

    Returns:
        operation.Operation: an `operation.Operation` object.

    """
    client = vmwareengine_v1.VmwareEngineClient()
    return client.delete_vmware_engine_network(
        name=f"projects/{project_id}/"
        f"locations/{region}/"
        f"vmwareEngineNetworks/{region}-default"
    )

def get_operation_by_name(operation_name: str) -> Operation:
    """
    Retrieves an Operation object from the VMware Engine API by its name.

    Args:
        operation_name (str): name of the operation to retrieve, which is used by
            the `VmwareEngineClient` to identify and fetch the appropriate operation
            from the API.

    Returns:
        Operation: an instance of the `Operation` class containing details of the
        specified operation.

    """
    client = vmwareengine_v1.VmwareEngineClient()
    request = GetOperationRequest()
    request.name = operation_name
    return client.get_operation(request)


def list_locations(project_id: str) -> str:
    """
    Takes a project ID as input, makes a request to the VMware Engine API to list
    locations for that project, and prints or returns the response location
    information in a string format.

    Args:
        project_id (str): ID of a VMware project to which the locations will be retrieved.

    Returns:
        str: a list of locations for the given project ID.

    """
    client = vmwareengine_v1.VmwareEngineClient()
    request = ListLocationsRequest()
    request.name = f"projects/{project_id}"
    locations = client.list_locations(request)
    print(locations)
    return str(locations)


def get_crop_hint(path: str) -> MutableSequence[vision.Vertex]:
    # [START vision_crop_hints_tutorial_get_crop_hints]
   
    """
    Takes a string path as input, reads an image file using the `vision.ImageAnnotatorClient`,
    crops the image based on an aspect ratio of 1.77 using the `crop_hints` method,
    and returns the bounding vertices of the first crop hint obtained from the
    cropped image.

    Args:
        path (str): image file path to be processed and is expected to be a binary
            file containing the image data.

    Returns:
        MutableSequence[vision.Vertex]: a sequence of `vision.Vertex` objects
        representing the bounding polyhedron for the first crop hint with an aspect
        ratio of 1.77.

    """
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
    """
    Uses the `get_crop_hint()` method to obtain a set of coordinate values, then
    draws a red polygon on top of an input image using Python's `ImageDraw` module
    and saves the modified image as "output-hint.jpg".

    Args:
        image_file (str): image file to be cropped and manipulated with the
            `get_crop_hint()` function and drawn on using `ImageDraw.Draw()`.

    """
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
    """
    Takes an image file path as input and crops the image using the crop hints
    provided by `get_crop_hint`. It saves the cropped image to a new file with the
    same name but with the `.jpg` extension.

    Args:
        image_file (str): path to an image file that will be cropped according to
            the provided crop hints.

    """
    vects = get_crop_hint(image_file)

    im = Image.open(image_file)
    im2 = im.crop([vects[0].x, vects[0].y, vects[2].x - 1, vects[2].y - 1])
    im2.save("output-crop.jpg", "JPEG")
    print("Saved new image to output-crop.jpg")


def create_live_session(
    project_id: str, location: str, live_config_id: str
) -> stitcher_v1.types.LiveSession:

    """
    Creates a new LiveSession object within the specified project and location,
    using the given live config ID as a reference. It returns the newly created
    LiveSession object.

    Args:
        project_id (str): 12-digit ID of a Google Cloud project that contains the
            location where the live session will be created.
        location (str): location of the video stitching project in the Google
            Cloud, which is used to generate the live session.
        live_config_id (str): ID of the live configuration that will be used to
            create a new live session.

    Returns:
        stitcher_v1.types.LiveSession: a `LiveSession` object with the created
        live configuration.

    """
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

    """
    Retrieves details of a live ad tag specified by ID, project ID, location and
    session ID.

    Args:
        project_id (str): identification number of a particular project being
            utilized to obtain details of a live ad tag within that project.
        location (str): location of the ad tag detail to be retrieved, which is
            used to generate the URL for retrieving the ad tag detail from the
            Video Stitcher service.
        session_id (str): 12-digit session ID that is used to identify a specific
            ad tag detail within a live streaming event.
        ad_tag_detail_id (str): ID of the specific live ad tag detail to retrieve
            from the Video Stitcher Service, which is used to filter and identify
            the desired ad tag detail in the response.

    Returns:
        stitcher_v1.types.LiveAdTagDetail: a `LiveAdTagDetail` object containing
        information about the specified live ad tag.

    """
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
  
    """
    Retrieves VOD ad tag detail information for a given project, location, session
    ID, and ad tag detail ID using the VideoStitcherServiceClient.

    Args:
        project_id (str): ID of the project in which the VOD ad tag detail is to
            be retrieved.
        location (str): location of the VOD ad tag detail to be retrieved, and is
            used in the client call to generate the complete path for fetching the
            ad tag detail from the Stitcher API.
        session_id (str): 12-digit session ID assigned to the ad tag by the Google
            Ad Manager platform.
        ad_tag_detail_id (str): ID of the VOD ad tag detail to retrieve from the
            VideoStitcher service.

    Returns:
        stitcher_v1.types.VodAdTagDetail: a `VodAdTagDetail` object containing
        information about the specified ad tag detail.

    """
    client = VideoStitcherServiceClient()

    name = client.vod_ad_tag_detail_path(
        project_id, location, session_id, ad_tag_detail_id
    )
    response = client.get_vod_ad_tag_detail(name=name)
    print(f"VOD ad tag detail: {response.name}")
    return response

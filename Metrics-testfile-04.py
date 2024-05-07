def delete_cluster(
    project_id: str, zone: str, private_cloud_name: str, cluster_name: str
) -> operation.Operation:
    """
    Deletes a specific cluster from a project, zone, and private cloud by calling
    the corresponding API method.

    Args:
        project_id (str): identifier of the project in which the private cloud is
            located, which is required to delete a cluster.
        zone (str): zone where the private cloud is located, which is necessary
            for identifying the correct location to delete the cluster within.
        private_cloud_name (str): name of the private cloud in which the cluster
            to be deleted is located.
        cluster_name (str): name of the cluster to be deleted.

    Returns:
        operation.Operation: an operation object representing the deletion of a cluster.

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
    Deletes a VMware network associated with a given project and region in the
    VMware Engine API.

    Args:
        project_id (str): ID of the project to which the network belongs, and is
            required for identifying the network to be deleted.
        region (str): location of the legacy network to be deleted within the
            specified project ID.

    Returns:
        operation.Operation: an operation object.

    """
    client = vmwareengine_v1.VmwareEngineClient()
    return client.delete_vmware_engine_network(
        name=f"projects/{project_id}/"
        f"locations/{region}/"
        f"vmwareEngineNetworks/{region}-default"
    )

def get_operation_by_name(operation_name: str) -> Operation:
    """
    Retrieves an Operation object based on its name from the VMware Engine API.

    Args:
        operation_name (str): name of the operation to retrieve in the GetOperationRequest
            message sent to the VmwareEngineClient object, and it is used to
            identify the desired operation in the response.

    Returns:
        Operation: an instance of the `Operation` class representing the specified
        operation.

    """
    client = vmwareengine_v1.VmwareEngineClient()
    request = GetOperationRequest()
    request.name = operation_name
    return client.get_operation(request)


def list_locations(project_id: str) -> str:
    """
    Receives a project ID as input and uses the `VmwareEngineClient` class to list
    locations for that project. It then prints the locations and returns them as
    a string.

    Args:
        project_id (str): identifier of the project for which the list of locations
            is being requested.

    Returns:
        str: a list of location objects for the given project ID.

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
    Reads an image file, generates crop hints for it using a provided aspect ratio,
    and returns the vertices of the first crop hint bounding polygon.

    Args:
        path (str): path to an image file that will be processed by the
            `vision.ImageAnnotatorClient()` method to generate crop hints.

    Returns:
        MutableSequence[vision.Vertex]: a sequence of `vision.Vertex` objects
        representing the bounds of the first crop hint based on an aspect ratio
        of 1.77.

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
    Opens an image file, draws a polygon around the crop hint, saves the new image
    as "output-hint.jpg", and prints a message indicating the success of the operation.

    Args:
        image_file (str): image to be processed and cropped, and is used to load
            the image into the function for processing.

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
    Crops an image based on a set of crop hints extracted from a separate file.

    Args:
        image_file (str): image file to be cropped.

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
    Creates a new Live Session in VideoStitcher service based on given project ID,
    location, and live config ID. It returns the newly created Live Session object.

    Args:
        project_id (str): 14-digit ID of a Google Cloud project that is used to
            identify the project and location for creating a live session.
        location (str): location of the live streaming event, which is used to
            generate the live session configuration.
        live_config_id (str): ID of the live configuration that will be used to
            create the new live session.

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
    Retrieves live ad tag detail information from a video stitcher service client
    using the given project ID, location, session ID, and ad tag detail ID.

    Args:
        project_id (str): 12-digit unique identifier of the Google Ads project
            associated with the live ad tag detail to be retrieved.
        location (str): location of the live ad tag detail to be retrieved, which
            is required to filter the ad tags in the Stitcher video platform.
        session_id (str): identifier of the session for which the live ad tag
            detail is being requested.
        ad_tag_detail_id (str): ID of the specific live ad tag detail for which
            details are to be retrieved.

    Returns:
        stitcher_v1.types.LiveAdTagDetail: a `LiveAdTagDetail` object containing
        details of a specific live ad tag.

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
    Retrieves the details of a specific VOD ad tag from VideoStitcher service
    client, given the project ID, location, session ID and ad tag detail ID.

    Args:
        project_id (str): identifying identifier of the Google Cloud Project
            containing the VOD content for which ad tags are being analyzed.
        location (str): location where the VOD ad tag detail is located in the project.
        session_id (str): 12-digit identifier for a specific video session associated
            with the VOD ad tag detail, which is required to retrieve the detailed
            information of the ad tag from VideoStitcher.
        ad_tag_detail_id (str): 16-character ID for a specific VOD ad tag detail
            within a given project, location, and session.

    Returns:
        stitcher_v1.types.VodAdTagDetail: a `VodAdTagDetail` object containing the
        details of the specified VOD ad tag.

    """
    client = VideoStitcherServiceClient()

    name = client.vod_ad_tag_detail_path(
        project_id, location, session_id, ad_tag_detail_id
    )
    response = client.get_vod_ad_tag_detail(name=name)
    print(f"VOD ad tag detail: {response.name}")
    return response

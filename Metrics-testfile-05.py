def get_vod_session(
    project_id: str, location: str, session_id: str
) -> stitcher_v1.types.VodSession:
    

    """
    Retrieves a VOD session with the specified `project_id`, `location`, and
    `session_id` from VideoStitcher service using the provided `client`.

    Args:
        project_id (str): ID of the project to which the VOD session belongs.
        location (str): location of the VOD session to retrieve.
        session_id (str): identifier of the VOD session to be retrieved from VideoStitcherServiceClient.

    Returns:
        stitcher_v1.types.VodSession: a `VodSession` object containing information
        about the specified VOD session.

    """
    client = VideoStitcherServiceClient()

    name = client.vod_session_path(project_id, location, session_id)
    response = client.get_vod_session(name=name)
    print(f"VOD session: {response.name}")
    return response


def create_job_with_embedded_captions(
    project_id: str,
    location: str,
    input_video_uri: str,
    input_captions_uri: str,
    output_uri: str,
) -> transcoder_v1.types.resources.Job:

    """
    Creates a new job in the Transcoder Service and configures it to transcode an
    input video and associated captions.

    Args:
        project_id (str): project ID that the job will be created for.
        location (str): location of the project where the job will be created and
            processed.
        input_video_uri (str): 360p resolution video to be transcoded, which will
            be used as the source material for the job.
        input_captions_uri (str): URI of the caption file to be embedded into the
            output video.
        output_uri (str): URI where the transcoded video and captions will be
            stored after the job is completed.

    Returns:
        transcoder_v1.types.resources.Job: a Job object with the newly created
        transcoding job.

    """
    client = TranscoderServiceClient()

    parent = f"projects/{project_id}/locations/{location}"
    job = transcoder_v1.types.Job()
    job.output_uri = output_uri
    job.config = transcoder_v1.types.JobConfig(
        inputs=[
            transcoder_v1.types.Input(
                key="input0",
                uri=input_video_uri,
            ),
            transcoder_v1.types.Input(
                key="caption-input0",
                uri=input_captions_uri,
            ),
        ],
        edit_list=[
            transcoder_v1.types.EditAtom(
                key="atom0",
                inputs=["input0", "caption-input0"],
            ),
        ],
        elementary_streams=[
            transcoder_v1.types.ElementaryStream(
                key="video-stream0",
                video_stream=transcoder_v1.types.VideoStream(
                    h264=transcoder_v1.types.VideoStream.H264CodecSettings(
                        height_pixels=360,
                        width_pixels=640,
                        bitrate_bps=550000,
                        frame_rate=60,
                    ),
                ),
            ),
            transcoder_v1.types.ElementaryStream(
                key="audio-stream0",
                audio_stream=transcoder_v1.types.AudioStream(
                    codec="aac",
                    bitrate_bps=64000,
                ),
            ),
            transcoder_v1.types.ElementaryStream(
                key="cea-stream0",
                text_stream=transcoder_v1.types.TextStream(
                    codec="cea608",
                    mapping_=[
                        transcoder_v1.types.TextStream.TextMapping(
                            atom_key="atom0",
                            input_key="caption-input0",
                            input_track=0,
                        ),
                    ],
                    language_code="en-US",
                    display_name="English",
                ),
            ),
        ],
        mux_streams=[
            transcoder_v1.types.MuxStream(
                key="sd-hls",
                container="ts",
                elementary_streams=["video-stream0", "audio-stream0"],
            ),
            transcoder_v1.types.MuxStream(
                key="sd-dash",
                container="fmp4",
                elementary_streams=["video-stream0"],
            ),
            transcoder_v1.types.MuxStream(
                key="audio-dash",
                container="fmp4",
                elementary_streams=["audio-stream0"],
            ),
        ],
        manifests=[
            transcoder_v1.types.Manifest(
                file_name="manifest.m3u8",
                type_="HLS",
                mux_streams=["sd-hls"],
            ),
            transcoder_v1.types.Manifest(
                file_name="manifest.mpd",
                type_="DASH",
                mux_streams=["sd-dash", "audio-dash"],
            ),
        ],
    )
    response = client.create_job(parent=parent, job=job)
    print(f"Job: {response.name}")
    return response

def create_job_with_set_number_images_spritesheet(
    project_id: str,
    location: str,
    input_uri: str,
    output_uri: str,
) -> transcoder_v1.types.resources.Job:

    """
    Creates a new Transcoder job and generates two sprite sheets from the input
    video, storing them in a Google Cloud Storage (GCS) bucket.

    Args:
        project_id (str): 20-character ID of the Google Cloud project that contains
            the resources to be transcoded.
        location (str): location where the transcoding will take place and is used
            to create the job configuration.
        input_uri (str): URL of the video or image file to be processed by the
            Transcoder service.
        output_uri (str): location where the generated sprite sheets will be saved

    Returns:
        transcoder_v1.types.resources.Job: a Job resource with an ad-hoc configuration
        for generating sprite sheets from input video.

    """
    client = TranscoderServiceClient()

    parent = f"projects/{project_id}/locations/{location}"
    job = transcoder_v1.types.Job()
    job.input_uri = input_uri
    job.output_uri = output_uri
    job.config = transcoder_v1.types.JobConfig(
        # Create an ad-hoc job. For more information, see https://cloud.google.com/transcoder/docs/how-to/jobs#create_jobs_ad_hoc.
        # See all options for the job config at https://cloud.google.com/transcoder/docs/reference/rest/v1/JobConfig.
        elementary_streams=[
            # This section defines the output video stream.
            transcoder_v1.types.ElementaryStream(
                key="video-stream0",
                video_stream=transcoder_v1.types.VideoStream(
                    h264=transcoder_v1.types.VideoStream.H264CodecSettings(
                        height_pixels=360,
                        width_pixels=640,
                        bitrate_bps=550000,
                        frame_rate=60,
                    ),
                ),
            ),
            # This section defines the output audio stream.
            transcoder_v1.types.ElementaryStream(
                key="audio-stream0",
                audio_stream=transcoder_v1.types.AudioStream(
                    codec="aac", bitrate_bps=64000
                ),
            ),
        ],
        # This section multiplexes the output audio and video together into a container.
        mux_streams=[
            transcoder_v1.types.MuxStream(
                key="sd",
                container="mp4",
                elementary_streams=["video-stream0", "audio-stream0"],
            ),
        ],
        # Generate two sprite sheets from the input video into the GCS bucket. For more information, see
        # https://cloud.google.com/transcoder/docs/how-to/generate-spritesheet#generate_set_number_of_images.
        sprite_sheets=[
            # Generate a 10x10 sprite sheet with 64x32px images.
            transcoder_v1.types.SpriteSheet(
                file_prefix="small-sprite-sheet",
                sprite_width_pixels=64,
                sprite_height_pixels=32,
                column_count=10,
                row_count=10,
                total_count=100,
            ),
            # Generate a 10x10 sprite sheet with 128x72px images.
            transcoder_v1.types.SpriteSheet(
                file_prefix="large-sprite-sheet",
                sprite_width_pixels=128,
                sprite_height_pixels=72,
                column_count=10,
                row_count=10,
                total_count=100,
            ),
        ],
    )
    response = client.create_job(parent=parent, job=job)
    print(f"Job: {response.name}")
    return response

def get_live_session(
    project_id: str, location: str, session_id: str
) -> stitcher_v1.types.LiveSession:

    """
    Retrieves a live session from VideoStitcher service by providing the project
    ID, location, and session ID as input parameters. It returns the LiveSession
    object representing the session.

    Args:
        project_id (str): ID of the project that contains the live session being
            retrieved.
        location (str): location of the live session to be retrieved, which is
            required information for accessing the relevant live session in the
            Stitcher video platform.
        session_id (str): ID of a specific live session to be retrieved within the
            specified project and location.

    Returns:
        stitcher_v1.types.LiveSession: a `LiveSession` object containing information
        about a live session within a given project and location.

    """
    client = VideoStitcherServiceClient()

    name = client.live_session_path(project_id, location, session_id)
    response = client.get_live_session(name=name)
    print(f"Live session: {response.name}")
    return response

def list_assets(project_id: str, location: str) -> pagers.ListAssetsPager:

    """
    Within a LivestreamServiceClient, retrieves a list of assets in a specific
    location for a given project ID by calling the `list_assets` method on the
    client and printing each asset's name.

    Args:
        project_id (str): identifier of the project for which assets will be listed.
        location (str): location of the assets to be listed in the API call made
            by the `list_assets()` function.

    Returns:
        pagers.ListAssetsPager: a list of assets associated with the specified
        project and location.

    """
    client = LivestreamServiceClient()

    parent = f"projects/{project_id}/locations/{location}"
    page_result = client.list_assets(parent=parent)
    print("Assets:")

    responses = []
    for response in page_result:
        print(response.name)
        responses.append(response)

    return responses

def list_channels(project_id: str, location: str) -> pagers.ListChannelsPager:

    """
    Retrieves a list of Livestream channels for a given project and location by
    calling the `LivestreamServiceClient#listChannels` method, printing the channel
    names, and returning the list of channels.

    Args:
        project_id (str): ID of the Livestream project for which to list channels.
        location (str): location from which to list the channels.

    Returns:
        pagers.ListChannelsPager: a list of Livestream channels located at the
        specified project and location.

    """
    client = LivestreamServiceClient()

    parent = f"projects/{project_id}/locations/{location}"
    page_result = client.list_channels(parent=parent)
    print("Channels:")

    responses = []
    for response in page_result:
        print(response.name)
        responses.append(response)

    return responses


def list_inputs(project_id: str, location: str) -> pagers.ListInputsPager:

    """
    Lists all inputs associated with a project and a location by making API calls
    to the Livestream Service Client.

    Args:
        project_id (str): ID of the project for which to retrieve inputs.
        location (str): location for which inputs will be listed within a Livestream
            project identified by the `project_id`.

    Returns:
        pagers.ListInputsPager: a list of inputs for a Livestream project in a
        specific location.

    """
    client = LivestreamServiceClient()

    parent = f"projects/{project_id}/locations/{location}"
    page_result = client.list_inputs(parent=parent)
    print("Inputs:")

    responses = []
    for response in page_result:
        print(response.name)
        responses.append(response)

    return responses


def pic_to_text(infile: str) -> str:
  

    # Instantiates a client
    """
    Reads an image file, processes it through Google's Text Detector API, and
    returns the detected text.

    Args:
        infile (str): image file to be processed by the `vision.ImageAnnotatorClient()`
            client, which reads its content and performs text detection on it.

    Returns:
        str: the detected text within the input image.

    """
    client = vision.ImageAnnotatorClient()

    # Opens the input image file
    with open(infile, "rb") as image_file:
        content = image_file.read()

    image = vision.Image(content=content)

    # For dense text, use document_text_detection
    # For less dense text, use text_detection
    response = client.document_text_detection(image=image)
    text = response.full_text_annotation.text
    print(f"Detected text: {text}")

    return text

def create_glossary(
    languages: list,
    project_id: str,
    glossary_name: str,
    glossary_uri: str,
) -> str:
   

    # Instantiates a client
    """
    Creates a new glossary resource in a Google Cloud Platform project. It takes
    the project ID, glossary name, and a URI for the input data as inputs and uses
    the Translate API to create the glossary resource.

    Args:
        languages (list): list of language codes that the generated glossary will
            support.
        project_id (str): ID of the Google Cloud project in which the glossary
            will be created.
        glossary_name (str): name of the glossary that will be created, and it is
            used to assign a unique identifier to the new glossary resource.
        glossary_uri (str): URI of the glossary to be created, which is used as
            the input for the `GcsSource` object in the function.

    Returns:
        str: the name of the newly created glossary.

    """
    client = translate.TranslationServiceClient()

    # Designates the data center location that you want to use
    location = "us-central1"

    # Set glossary resource name
    name = client.glossary_path(project_id, location, glossary_name)

    # Set language codes
    language_codes_set = translate.Glossary.LanguageCodesSet(language_codes=languages)

    gcs_source = translate.GcsSource(input_uri=glossary_uri)

    input_config = translate.GlossaryInputConfig(gcs_source=gcs_source)

    # Set glossary resource information
    glossary = translate.Glossary(
        name=name, language_codes_set=language_codes_set, input_config=input_config
    )

    parent = f"projects/{project_id}/locations/{location}"

    # Create glossary resource
    # Handle exception for case in which a glossary
    #  with glossary_name already exists
    try:
        operation = client.create_glossary(parent=parent, glossary=glossary)
        operation.result(timeout=90)
        print("Created glossary " + glossary_name + ".")
    except AlreadyExists:
        print(
            "The glossary "
            + glossary_name
            + " already exists. No new glossary was created."
        )

    return glossary_name
    # [END translate_hybrid_create_glossary]

def initialize_tracer(project_id: str) -> TracerProvider:
    """
    Sets up an OpenTelemetry tracer provider, adds a span processor to trace Cloud
    Trace events, and sets global text mapping for OpenTelemetry tracing. It returns
    the OpenTelemetry tracer instance created.

    Args:
        project_id (str): ID of a project and is used to create a CloudTraceSpanExporter
            instance, which adds the project-specific trace exporter to the tracer
            provider, for transmitting span data to OpenTelemetry collectors.

    Returns:
        TracerProvider: an OpenTelemetry tracer provider.

    """
    trace.set_tracer_provider(TracerProvider())
    cloud_trace_exporter = CloudTraceSpanExporter(project_id)
    trace.get_tracer_provider().add_span_processor(
        SimpleSpanProcessor(cloud_trace_exporter)
    )
    propagate.set_global_textmap(CloudTraceFormatPropagator())
    opentelemetry_tracer = trace.get_tracer(__name__)

    return opentelemetry_tracer


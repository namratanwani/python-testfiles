def get_vod_session(
    project_id: str, location: str, session_id: str
) -> stitcher_v1.types.VodSession:
    

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

    client = VideoStitcherServiceClient()

    name = client.live_session_path(project_id, location, session_id)
    response = client.get_live_session(name=name)
    print(f"Live session: {response.name}")
    return response

def list_assets(project_id: str, location: str) -> pagers.ListAssetsPager:

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
    trace.set_tracer_provider(TracerProvider())
    cloud_trace_exporter = CloudTraceSpanExporter(project_id)
    trace.get_tracer_provider().add_span_processor(
        SimpleSpanProcessor(cloud_trace_exporter)
    )
    propagate.set_global_textmap(CloudTraceFormatPropagator())
    opentelemetry_tracer = trace.get_tracer(__name__)

    return opentelemetry_tracer


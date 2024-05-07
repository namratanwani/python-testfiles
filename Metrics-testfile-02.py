def list_tasks(
    project_id: str, region: str, job_name: str, group_name: str
) -> Iterable[batch_v1.Task]:
    """
    Provides an iterable of tasks based on a given project ID, region, job name,
    and task group name using the `BatchServiceClient`.

    Args:
        project_id (str): 1-based identifier of the Google Cloud Platform project
            for which tasks are to be listed.
        region (str): location of the job for which tasks need to be listed.
        job_name (str): name of the job for which tasks should be listed, and is
            used to filter the list of tasks returned by the `list_tasks()` method
            of the `BatchServiceClient`.
        group_name (str): name of the task group that the user wants to retrieve
            tasks for.

    Returns:
        Iterable[batch_v1.Task]: an iterable of batch v1 tasks.

    """
    client = batch_v1.BatchServiceClient()

    return client.list_tasks(
        parent=f"projects/{project_id}/locations/{region}/jobs/{job_name}/taskGroups/{group_name}"
    )

def print_job_logs(project_id: str, job: batch_v1.Job) -> NoReturn:
     # Initialize client that will be used to send requests across threads. This
    # client only needs to be created once, and can be reused for multiple requests.
    """
    Is used to retrieve job logs for a given project and log entry filter criteria.
    It initializes a logging client, creates a logger, lists entries with the
    filter criteria, and prints each log entry's payload.

    Args:
        project_id (str): unique identifier of the project for which the job logs
            are being retrieved.
        job (batch_v1.Job): Batch job whose logs are to be retrieved and printed.

    """
    log_client = logging.Client(project=project_id)
    logger = log_client.logger("batch_task_logs")

    for log_entry in logger.list_entries(filter_=f"labels.job_uid={job.uid}"):
        print(log_entry.payload)

def sample_cancel_operation(project, operation_id):

    """
    Cancels an operation with a specified project and operation ID using the `AutoMlClient`.

    Args:
        project ("Google Cloud Project ID".): Google Cloud Project ID for which
            an operation will be cancelled.
            
            		- `project`: This is a string that represents the ID of a Google
            Cloud Project. It is a required field and has a maximum length of 32
            characters.
            		- `operation_id`: This is a string that represents the ID of an
            operation within the project. It is a required field and has a maximum
            length of 255 characters.
        operation_id (str): ID of the operation to be cancelled.

    """
    client = automl_v1beta1.AutoMlClient()

    operations_client = client._transport.operations_client

    # project = '[Google Cloud Project ID]'
    # operation_id = '[Operation ID]'
    name = "projects/{}/locations/us-central1/operations/{}".format(
        project, operation_id
    )

    operations_client.cancel_operation(name)

    print(f"Cancelled operation: {name}")

def authenticate_with_api_key(quota_project_id: str, api_key_string: str) -> None:
    

    # Initialize the Language Service client and set the API key and the quota project id.
    """
    Uses an API key and a quota project ID to initialize a Language Service client
    and make requests to analyze the sentiment of text.

    Args:
        quota_project_id (str): ID of the project to which the API key is linked,
            which is required to authenticate the Language Service client.
        api_key_string (str): API key required to access the Language Service API,
            which is used to initialize the `LanguageServiceClient` and make
            requests to analyze sentiment of text.

    """
    client = language_v1.LanguageServiceClient(
        client_options={"api_key": api_key_string, "quota_project_id": quota_project_id}
    )

    text = "Hello, world!"
    document = language_v1.Document(
        content=text, type_=language_v1.Document.Type.PLAIN_TEXT
    )

    # Make a request to analyze the sentiment of the text.
    sentiment = client.analyze_sentiment(
        request={"document": document}
    ).document_sentiment

    print(f"Text: {text}")
    print(f"Sentiment: {sentiment.score}, {sentiment.magnitude}")
    print("Successfully authenticated using the API key")
          
def create_api_key(project_id: str, suffix: str) -> Key:
       # Create the API Keys client.
    """
    Creates a new API key for a given project and location, returns the created key.

    Args:
        project_id (str): identifier of the Google Cloud Platform project where
            the API key will be created, which is required as a parent resource
            for the API key's location in the CreateKeyRequest message.
        suffix (str): 30-character suffix to be appended to the generated API key,
            which allows multiple keys to be created for the same project with
            unique names based on their suffixes.

    Returns:
        Key: a `Key` object containing the created API key information.

    """
    client = api_keys_v2.ApiKeysClient()

    key = api_keys_v2.Key()
    key.display_name = f"My first API key - {suffix}"

    # Initialize request and set arguments.
    request = api_keys_v2.CreateKeyRequest()
    request.parent = f"projects/{project_id}/locations/global"
    request.key = key

    # Make the request and wait for the operation to complete.
    response = client.create_key(request=request).result()

    print(f"Successfully created an API key: {response.name}")
    # For authenticating with the API key, use the value in ""response.key_string"".
    # To restrict the usage of this API key, use the value in ""response.name"".
    return response

def lookup_api_key(api_key_string: str) -> None:
   
    # Create the API Keys client.
    """
    Creates an instance of the `ApiKeysClient`, initializes a `LookupKeyRequest`
    object with the API key string, and makes a request to the Google Cloud API
    to retrieve the name of the API key. The response is then printed to the console.

    Args:
        api_key_string (str): 12-digit alphanumeric API key to be looked up.

    """
    client = api_keys_v2.ApiKeysClient()

    # Initialize the lookup request and set the API key string.
    lookup_key_request = api_keys_v2.LookupKeyRequest(
        key_string=api_key_string,
        # Optionally, you can also set the etag (version).
        # etag=etag,
    )

    # Make the request and obtain the response.
    lookup_key_response = client.lookup_key(lookup_key_request)

    print(f"Successfully retrieved the API key name: {lookup_key_response.name}")

    
def restrict_api_key_android(project_id: str, key_id: str) -> Key:

    # Create the API Keys client.
    """
    Updates an API key's restrictions for Android applications, restricting its
    use to a single application with a specified package name and SHA1 fingerprint.

    Args:
        project_id (str): 12-digit project number used to identify the Google Cloud
            Platform project that the API key will be restricted for.
        key_id (str): 256-bit long API key identifier that needs to be updated
            with restrictions for an android application.

    Returns:
        Key: a success message indicating that the API key has been updated with
        restrictions on Android application usage.

    """
    client = api_keys_v2.ApiKeysClient()

    # Specify the android application's package name and SHA1 fingerprint.
    allowed_application = api_keys_v2.AndroidApplication()
    allowed_application.package_name = "com.google.appname"
    allowed_application.sha1_fingerprint = "0873D391E987982FBBD30873D391E987982FBBD3"

    # Restrict the API key usage by specifying the allowed applications.
    android_key_restriction = api_keys_v2.AndroidKeyRestrictions()
    android_key_restriction.allowed_applications = [allowed_application]

    # Set the restriction(s).
    # For more information on API key restriction, see:
    # https://cloud.google.com/docs/authentication/api-keys
    restrictions = api_keys_v2.Restrictions()
    restrictions.android_key_restrictions = android_key_restriction

    key = api_keys_v2.Key()
    key.name = f"projects/{project_id}/locations/global/keys/{key_id}"
    key.restrictions = restrictions

    # Initialize request and set arguments.
    request = api_keys_v2.UpdateKeyRequest()
    request.key = key
    request.update_mask = "restrictions"

    # Make the request and wait for the operation to complete.
    response = client.update_key(request=request).result()

    print(f"Successfully updated the API key: {response.name}")
    # Use response.key_string to authenticate.
    return response


def restrict_api_key_api(project_id: str, key_id: str) -> Key:
    
    # Create the API Keys client.
    """
    Restricts an API key's usage by specifying a target service and methods, making
    it usable only for those methods in that service.

    Args:
        project_id (str): 25-character ID of the Google Cloud Project that contains
            the API key being restricted, which is required to specify the correct
            project for the API key's restriction.
        key_id (str): ID of an existing API key that is being updated with
            restrictions on its usage.

    Returns:
        Key: a successful update of the API key with restricted usage.

    """
    client = api_keys_v2.ApiKeysClient()

    # Restrict the API key usage by specifying the target service and methods.
    # The API key can only be used to authenticate the specified methods in the service.
    api_target = api_keys_v2.ApiTarget()
    api_target.service = "translate.googleapis.com"
    api_target.methods = ["transate.googleapis.com.TranslateText"]

    # Set the API restriction(s).
    # For more information on API key restriction, see:
    # https://cloud.google.com/docs/authentication/api-keys
    restrictions = api_keys_v2.Restrictions()
    restrictions.api_targets = [api_target]

    key = api_keys_v2.Key()
    key.name = f"projects/{project_id}/locations/global/keys/{key_id}"
    key.restrictions = restrictions

    # Initialize request and set arguments.
    request = api_keys_v2.UpdateKeyRequest()
    request.key = key
    request.update_mask = "restrictions"

    # Make the request and wait for the operation to complete.
    response = client.update_key(request=request).result()

    print(f"Successfully updated the API key: {response.name}")
    # Use response.key_string to authenticate.
    return response

def restrict_api_key_http(project_id: str, key_id: str) -> Key:
    
    # Create the API Keys client.
    """
    Updates an API key's restrictions, limiting its usage to specific websites by
    adding them to the list of allowed referrers.

    Args:
        project_id (str): ID of the Google Cloud Platform project that the API key
            belongs to and is required to update the key's restrictions.
        key_id (str): ID of the API key to be restricted.

    Returns:
        Key: the updated API key with restrictions on usage for specific websites.

    """
    client = api_keys_v2.ApiKeysClient()

    # Restrict the API key usage to specific websites by adding them to the list of allowed_referrers.
    browser_key_restrictions = api_keys_v2.BrowserKeyRestrictions()
    browser_key_restrictions.allowed_referrers = ["www.example.com/*"]

    # Set the API restriction.
    # For more information on API key restriction, see:
    # https://cloud.google.com/docs/authentication/api-keys
    restrictions = api_keys_v2.Restrictions()
    restrictions.browser_key_restrictions = browser_key_restrictions

    key = api_keys_v2.Key()
    key.name = f"projects/{project_id}/locations/global/keys/{key_id}"
    key.restrictions = restrictions

    # Initialize request and set arguments.
    request = api_keys_v2.UpdateKeyRequest()
    request.key = key
    request.update_mask = "restrictions"

    # Make the request and wait for the operation to complete.
    response = client.update_key(request=request).result()

    print(f"Successfully updated the API key: {response.name}")
    # Use response.key_string to authenticate.
    return response


def restrict_api_key_ios(project_id: str, key_id: str) -> Key:

    # Create the API Keys client.
    """
    Restricts an API key's usage for iOS apps by specifying allowed bundle IDs.

    Args:
        project_id (str): ID of the Google Cloud Platform project for which the
            API key is being restricted, and it is used to identify the project
            in the request to update the API key restrictions.
        key_id (str): ID of the API key for which restrictions are being updated.

    Returns:
        Key: a successful update of an API key with restricted usage for iOS apps.

    """
    client = api_keys_v2.ApiKeysClient()

    # Restrict the API key usage by specifying the bundle ID(s) of iOS app(s) that can use the key.
    ios_key_restrictions = api_keys_v2.IosKeyRestrictions()
    ios_key_restrictions.allowed_bundle_ids = ["com.google.gmail", "com.google.drive"]

    # Set the API restriction.
    # For more information on API key restriction, see:
    # https://cloud.google.com/docs/authentication/api-keys
    restrictions = api_keys_v2.Restrictions()
    restrictions.ios_key_restrictions = ios_key_restrictions

    key = api_keys_v2.Key()
    key.name = f"projects/{project_id}/locations/global/keys/{key_id}"
    key.restrictions = restrictions

    # Initialize request and set arguments.
    request = api_keys_v2.UpdateKeyRequest()
    request.key = key
    request.update_mask = "restrictions"

    # Make the request and wait for the operation to complete.
    response = client.update_key(request=request).result()

    print(f"Successfully updated the API key: {response.name}")
    # Use response.key_string to authenticate.
    return response

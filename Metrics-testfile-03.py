def restrict_api_key_server(project_id: str, key_id: str) -> Key:
  
    # Create the API Keys client.
    """
    Updates an API key's restrictions by specifying IP addresses or subnets that
    are allowed or denied.

    Args:
        project_id (str): ID of the Google Cloud Platform project for which an API
            key is being updated, and it is required to specify the project to
            which the key belongs.
        key_id (str): ID of an API key for which restrictions will be applied.

    Returns:
        Key: a success message indicating that the API key has been updated with
        new restrictions.

    """
    client = api_keys_v2.ApiKeysClient()

    # Restrict the API key usage by specifying the IP addresses.
    # You can specify the IP addresses in IPv4 or IPv6 or a subnet using CIDR notation.
    server_key_restrictions = api_keys_v2.ServerKeyRestrictions()
    server_key_restrictions.allowed_ips = ["198.51.100.0/24", "2000:db8::/64"]

    # Set the API restriction.
    # For more information on API key restriction, see:
    # https://cloud.google.com/docs/authentication/api-keys
    restrictions = api_keys_v2.Restrictions()
    restrictions.server_key_restrictions = server_key_restrictions

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


def is_ipv6(addr):
    """
    Checks whether a given IP address is an IPv6 address or not by trying to convert
    it into an IPv6 format using `socket.inet_pton()` and detecting any error
    messages. If the conversion succeeds, the function returns `True`, otherwise
    it returns `False`.

    Args:
        addr (str): address to be tested for IPv6 format, and it is passed to the
            `socket.inet_pton()` function to determine if it can be converted into
            an IPv6 address.

    Returns:
        bool: a boolean value indicating whether the given address is an IPv6 address.

    """
    try:
        socket.inet_pton(socket.AF_INET6, addr)
        return True
    except OSError:
        return False


def index():
    """
    Logs the client IP address to a temporary file and returns the instance ID and
    log message as output.

    Returns:
        str: a concatenation of instance ID and IP address seen in the request.

    """
    instance_id = os.environ.get("GAE_INSTANCE", "1")

    user_ip = request.remote_addr

    # Keep only the first two octets of the IP address.
    if is_ipv6(user_ip):
        user_ip = ":".join(user_ip.split(":")[:2])
    else:
        user_ip = ".".join(user_ip.split(".")[:2])

    with open("/tmp/seen.txt", "a") as f:
        f.write(f"{user_ip}\n")

    with open("/tmp/seen.txt") as f:
        seen = f.read()

    output = f"Instance: {instance_id}\nSeen:{seen}"
    return output, 200, {"Content-Type": "text/plain; charset=utf-8"}

def server_error(e):
    """
    Logs an exception to the error log and returns a 500 status code along with a
    message containing the full stack trace in the pre tag.

    Args:
        e (exception object/value.): exception or error that occurred during a
            request and is logged along with its detailed stack trace.
            
            		- `logging.exception("An error occurred during a request.")`: This
            statement logs an exception message in the server's log file for further
            analysis. The exception is passed to the logging function without any
            additional processing.
            		- `return`: This line of code returns an HTTP status code of 500
            (Internal Server Error) to indicate that the server has encountered a
            problem that prevented it from fulfilling the request.
            		- `<pre>{e}</pre>`: This is the actual error object or data structure
            passed to the `server_error` function, which contains details about
            the error.
            		- `<br>See logs for full stacktrace.>`: This is a statement that
            encourages users to view the server's log file for additional information
            on the error, including the complete stack trace of the error.

    Returns:
        int: a message containing the error details followed by a HTTP status code
        of 500.

    """
    logging.exception("An error occurred during a request.")
    return (
        f"An internal error occurred: <pre>{e}</pre><br>See logs for full stacktrace.",
        500,
    )


def submit_uri(project_id: str, uri: str) -> Submission:
    """
    Takes in a project ID and a URL to be analyzed for security threats using
    WebRisk. It creates a submission object, sets the URI, threat confidence level,
    and justification, and adds details on how the threat was discovered. Then it
    submits the request to WebRisk for analysis and returns the response.

    Args:
        project_id (str): project to which the URI will be submitted for analysis.
        uri (str): string value that will be analyzed by the WebRisk API for
            potential safety threats, and it is passed to the `Submission` object
            as part of the `SubmitUriRequest`.

    Returns:
        Submission: a `SubmitUriResponse` object containing details of the submitted
        URI and the abuse detected.

    """
    webrisk_client = webrisk_v1.WebRiskServiceClient()

    # Set the URI to be submitted.
    submission = webrisk_v1.Submission()
    submission.uri = uri

    # Confidence that a URI is unsafe.
    threat_confidence = webrisk_v1.ThreatInfo.Confidence(
        level=webrisk_v1.ThreatInfo.Confidence.ConfidenceLevel.MEDIUM
    )

    # Context about why the URI is unsafe.
    threat_justification = webrisk_v1.ThreatInfo.ThreatJustification(
        # Labels that explain how the URI was classified.
        labels=[
            webrisk_v1.ThreatInfo.ThreatJustification.JustificationLabel.AUTOMATED_REPORT
        ],
        # Free-form context on why this URI is unsafe.
        comments=["Testing submission"],
    )

    # Set the context about the submission including the type of abuse found on the URI and
    # supporting details.
    threat_info = webrisk_v1.ThreatInfo(
        # The abuse type found on the URI.
        abuse_type=webrisk_v1.types.ThreatType.SOCIAL_ENGINEERING,
        threat_confidence=threat_confidence,
        threat_justification=threat_justification,
    )

    # Set the details about how the threat was discovered.
    threat_discovery = webrisk_v1.ThreatDiscovery(
        # Platform on which the threat was discovered.
        platform=webrisk_v1.ThreatDiscovery.Platform.MACOS,
        # CLDR region code of the countries/regions the URI poses a threat ordered
        # from most impact to least impact. Example: ""US"" for United States.
        region_codes=["US"],
    )

    request = webrisk_v1.SubmitUriRequest(
        parent=f"projects/{project_id}",
        submission=submission,
        threat_info=threat_info,
        threat_discovery=threat_discovery,
    )

    response = webrisk_client.submit_uri(request).result(timeout=30)
    return response


def create_cluster(
    project_id: str,
    zone: str,
    private_cloud_name: str,
    cluster_name: str,
    node_count: int = 4,
) -> operation.Operation:
        
    """
    Creates a cluster on VMWare Engine. It takes as input the project ID, zone,
    private cloud name, cluster name, and node count and generates a `CreateClusterRequest`
    object to create the cluster.

    Args:
        project_id (str): ID of the Google Cloud Platform project that contains
            the private cloud where the cluster will be created.
        zone (str): Azure location where the private cloud exists, which is used
            as the parent of the create cluster request.
        private_cloud_name (str): name of the private cloud where the cluster will
            be created within, as specified in the parent field of the
            CreateClusterRequest message.
        cluster_name (str): name of the cluster to be created.
        node_count (4): number of nodes to be created in the cluster.

    Returns:
        operation.Operation: an `operation.Operation` object, representing the
        created cluster resource.

    """
    if node_count < 3:
        raise ValueError("Cluster needs to have at least 3 nodes")

    request = vmwareengine_v1.CreateClusterRequest()
    request.parent = (
        f"projects/{project_id}/locations/{zone}/privateClouds/{private_cloud_name}"
    )

    request.cluster = vmwareengine_v1.Cluster()
    request.cluster.name = cluster_name

    # Currently standard-72 is the only supported node type.
    request.cluster.node_type_configs = {
        "standard-72": vmwareengine_v1.NodeTypeConfig()
    }
    request.cluster.node_type_configs["standard-72"].node_count = node_count

    client = vmwareengine_v1.VmwareEngineClient()
    return client.create_cluster(request)


def create_custom_cluster(
    project_id: str,
    zone: str,
    private_cloud_name: str,
    cluster_name: str,
    node_count: int = 4,
    core_count: int = 28,
) -> operation.Operation:
    
    """
    Creates a new cluster on VMWare Engine. It takes in project id, zone, private
    cloud name and the cluster name, and it creates the node configuration with
    custom core count based on the user input.

    Args:
        project_id (str): identifier of a Google Cloud project that the custom
            cluster will be created in.
        zone (str): name of the GCP zone where the private cloud is located, which
            is used to identify the location of the private cloud and its associated
            resources in the VMware Engine API request.
        private_cloud_name (str): name of the private cloud where the custom cluster
            will be created within, and it is required to specify the correct
            project and location for the cluster's creation.
        cluster_name (str): name of the cluster that will be created.
        node_count (4): number of nodes in the custom cluster being created, and
            it is required to be greater than or equal to 3.
        core_count (28): number of custom cores to assign to each node in the
            cluster, which is specified in the `node_type_configs` dictionary
            within the `CreateClusterRequest` object.

    Returns:
        operation.Operation: an `operation.Operation` object, which represents the
        created cluster.

    """
    if node_count < 3:
        raise ValueError("Cluster needs to have at least 3 nodes")

    request = vmwareengine_v1.CreateClusterRequest()
    request.parent = (
        f"projects/{project_id}/locations/{zone}/privateClouds/{private_cloud_name}"
    )

    request.cluster = vmwareengine_v1.Cluster()
    request.cluster.name = cluster_name

    # Currently standard-72 is the only supported node type.
    request.cluster.node_type_configs = {
        "standard-72": vmwareengine_v1.NodeTypeConfig()
    }
    request.cluster.node_type_configs["standard-72"].node_count = node_count
    request.cluster.node_type_configs["standard-72"].custom_core_count = core_count

    client = vmwareengine_v1.VmwareEngineClient()
    return client.create_cluster(request)


def create_legacy_network(
    project_id: str, region: str
) -> vmwareengine_v1.VmwareEngineNetwork:
    
    """
    Creates a VMware legacy network using the `VmwareEngineClient` and returns the
    resulting `VmwareEngineNetwork`.

    Args:
        project_id (str): identifier of a Google Cloud Platform project that the
            created legacy network will belong to.
        region (str): location where the legacy network will be created, and it
            is used as the parent resource for the creation of the legacy network
            within the vmwareengine API.

    Returns:
        vmwareengine_v1.VmwareEngineNetwork: a `VmwareEngineNetwork` object
        containing the created network's details.

    """
    network = vmwareengine_v1.VmwareEngineNetwork()
    network.description = (
        "Legacy network created using vmwareengine_v1.VmwareEngineNetwork"
    )
    network.type_ = vmwareengine_v1.VmwareEngineNetwork.Type.LEGACY

    request = vmwareengine_v1.CreateVmwareEngineNetworkRequest()
    request.parent = f"projects/{project_id}/locations/{region}"
    request.vmware_engine_network_id = f"{region}-default"
    request.vmware_engine_network = network

    client = vmwareengine_v1.VmwareEngineClient()
    result = client.create_vmware_engine_network(request, timeout=TIMEOUT).result()

    return result


def create_network_policy(
    project_id: str,
    region: str,
    ip_range: str,
    internet_access: bool,
    external_ip: bool,
) -> operation.Operation:
    
    """
    Creates a NetworkPolicy resource on the VMware Engine API for given project
    ID, region, and IP range, enabling internet access, external IP, and specifying
    CIDR block for the edge services.

    Args:
        project_id (str): identifier of a specific project in VMware Engine.
        region (str): location where the network policy will be created and applied,
            and is used to identify the default network for the project in the
            specified region.
        ip_range (str): CIDR block of the network that will be assigned to the
            virtual machines, and it must end with the `/26` suffix to indicate
            an RFC 1918 CIDR block.
        internet_access (bool): enable state of the network policy's internet
            access feature, with a value of `true` enabling and `false` disabling
            it.
        external_ip (bool): value of the "External IP" field within the `NetworkPolicy`
            resource, which determines whether the network policy allows or denies
            access to the external internet.

    Returns:
        operation.Operation: a `operation.Operation` object containing the created
        network policy details.

    """
    if not ip_range.endswith("/26"):
        raise ValueError(
            "The ip_range needs to be an RFC 1918 CIDR block with a '/26' suffix"
        )

    network_policy = vmwareengine_v1.NetworkPolicy()
    network_policy.vmware_engine_network = f"projects/{project_id}/locations/{region}/vmwareEngineNetworks/{region}-default"
    network_policy.edge_services_cidr = ip_range
    network_policy.internet_access.enabled = internet_access
    network_policy.external_ip.enabled = external_ip

    request = vmwareengine_v1.CreateNetworkPolicyRequest()
    request.network_policy = network_policy
    request.parent = f"projects/{project_id}/locations/{region}"
    request.network_policy_id = f"{region}-default"

    client = vmwareengine_v1.VmwareEngineClient()
    return client.create_network_policy(request)


def create_private_cloud(
    project_id: str, zone: str, network_name: str, cloud_name: str, cluster_name: str
) -> operation.Operation:
 
    """
    Creates a private cloud instance in VMware Engine with given project ID, zone,
    network name and cloud name. It sets up a management cluster, configures the
    node count, and defines the network configuration.

    Args:
        project_id (str): ID of the Google Cloud Project where the private cloud
            will be created.
        zone (str): zone where the private cloud will be created, and it is used
            to specify the parent resource for the private cloud in the
            CreatePrivateCloudRequest message.
        network_name (str): name of the network to be used for the private cloud,
            which is then configured in the `network_config` part of the request.
        cloud_name (str): 12-characters ID of the private cloud that will be created.
        cluster_name (str): ID of the management cluster that will be created
            within the private cloud.

    Returns:
        operation.Operation: an `operation.Operation` object representing the
        creation of a private cloud.

    """
    request = vmwareengine_v1.CreatePrivateCloudRequest()
    request.parent = f"projects/{project_id}/locations/{zone}"
    request.private_cloud_id = cloud_name

    request.private_cloud = vmwareengine_v1.PrivateCloud()
    request.private_cloud.management_cluster = (
        vmwareengine_v1.PrivateCloud.ManagementCluster()
    )
    request.private_cloud.management_cluster.cluster_id = cluster_name

    node_config = vmwareengine_v1.NodeTypeConfig()
    node_config.node_count = DEFAULT_NODE_COUNT

    # Currently standard-72 is the only supported node type.
    request.private_cloud.management_cluster.node_type_configs = {
        "standard-72": node_config
    }

    request.private_cloud.network_config = vmwareengine_v1.NetworkConfig()
    request.private_cloud.network_config.vmware_engine_network = network_name
    request.private_cloud.network_config.management_cidr = DEFAULT_MANAGEMENT_CIDR

    client = vmwareengine_v1.VmwareEngineClient()
    return client.create_private_cloud(request)

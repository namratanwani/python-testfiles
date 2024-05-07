def restrict_api_key_server(project_id: str, key_id: str) -> Key:
  
    # Create the API Keys client.
    """
    Updates an API key's restrictions by specifying a list of allowed IP addresses.

    Args:
        project_id (str): ID of the Google Cloud Project that the API key belongs
            to and is required to specify the project context for the restriction
            update operation.
        key_id (str): 26-character key ID of an API key to be restricted, which
            is used to update the restrictions on that specific key.

    Returns:
        Key: the updated API key information with restricted usage based on specified
        IP addresses.

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
    Determines if an IP address is in IP version 6 (IPv6) format by using the
    `socket.inet_pton()` method to convert the address to an IPv6 representation
    and then checking if it succeeds without raising an error. If it does, the
    function returns `True`, otherwise it returns `False`.

    Args:
        addr (str): 32-bit IP address to be checked for IPv6 compatibility using
            the `socket.inet_pton()` method.

    Returns:
        bool: a boolean value indicating whether the provided address is an IPv6
        address.

    """
    try:
        socket.inet_pton(socket.AF_INET6, addr)
        return True
    except OSError:
        return False


def index():
    """
    Logs the remote user's IP address to a temporary file, then reads and returns
    that log message as output.

    Returns:
        str: a string consisting of two parts: the instance ID and a list of IP
        addresses seen by the function.

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
    Generates a server-side error message with an HTML formatted stack trace when
    an internal error occurs during a request.

    Args:
        e (Exception.): internal error that occurred during a request, which is
            passed to the function as an exception.
            
            		- `e`: The deserialized input object containing the details of the
            error that occurred during a request. Its attributes and properties
            can vary depending on the specific implementation and usage.
            
            	The function then returns a response with the message "An internal
            error occurred" followed by the full stacktrace in a HTML format, along
            with a status code of 500.

    Returns:
        : 500: a string of text indicating that an internal error occurred, along
        with the HTTP status code 500.
        
        		- `500`: The HTTP status code indicating that an internal server error
        occurred.

    """
    logging.exception("An error occurred during a request.")
    return (
        f"An internal error occurred: <pre>{e}</pre><br>See logs for full stacktrace.",
        500,
    )


def submit_uri(project_id: str, uri: str) -> Submission:
    """
    Takes a project ID and a URI to submit to WebRisk for analysis, then creates
    a submission object with relevant contextual information and submits it to the
    WebRisk API for threat analysis.

    Args:
        project_id (str): project ID associated with the URI to be submitted for
            analysis.
        uri (str): string that is to be checked for abuse by WebRisk Service.

    Returns:
        Submission: a `SubmitUriResponse` object containing information about the
        submitted URI.

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
    Creates a new cluster within a private cloud project. It requires project ID,
    zone, and the name for the cluster. The function also specifies the number of
    nodes required in the cluster

    Args:
        project_id (str): identifier of a Google Cloud Platform project to which
            the cluster will be created.
        zone (str): location where the cluster will be created in the user's Private
            Cloud.
        private_cloud_name (str): name of the private cloud where the cluster will
            be created.
        cluster_name (str): name of the cluster that will be created, which is
            required to identify the new cluster in the API response.
        node_count (4): number of nodes in the cluster being created, which must
            be greater than or equal to 3 according to the function's logic.

    Returns:
        operation.Operation: an `operation.Operation` object.

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
    Creates a custom cluster on a specified private cloud within a project,
    specifying the cluster name, number of nodes, and core count.

    Args:
        project_id (str): ID of the project in which the custom cluster will be created.
        zone (str): location where the private cloud is hosted, which is used to
            generate the correct URL for the create cluster request.
        private_cloud_name (str): name of the private cloud where the cluster will
            be created within.
        cluster_name (str): name of the custom cluster being created.
        node_count (4): number of nodes in the custom cluster to be created, which
            must be greater than or equal to 3.
        core_count (28): number of custom cores to be allocated to each node in
            the cluster.

    Returns:
        operation.Operation: an operation object representing the creation of a
        custom cluster in VMware.

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
    Creates a legacy network in the specified region and project ID using the
    VMware Engine API.

    Args:
        project_id (str): ID of the Google Cloud Platform project to which the
            legacy network will be created.
        region (str): location where the legacy network will be created within the
            project specified by the `project_id`.

    Returns:
        vmwareengine_v1.VmwareEngineNetwork: a `VmwareEngineNetwork` object
        representing a legacy network.

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
    Creates a network policy in the specified region and project ID. It sets the
    IP range, internet access, and external IP settings for the policy, and then
    creates the policy using the `vmwareengine` API.

    Args:
        project_id (str): identifier of the Google Cloud Platform project that the
            network policy will be created for and is used to identify the location
            of the network policy in the client's API calls.
        region (str): region where the network policy will be created, and it is
            used to determine the ID of the default virtual network within that region.
        ip_range (str): CIDR block of the network for which the policy is being
            created, and it must end with the `/26` suffix to be valid.
        internet_access (bool): enabled status of internet access for the network
            policy.
        external_ip (bool): boolean value whether to enable the external IP address
            of the network policy.

    Returns:
        operation.Operation: a `operation.Operation` object containing the newly
        created network policy.

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
    Creates a private cloud instance in a given project, zone, and network, with
    a specified management cluster name and node type configuration.

    Args:
        project_id (str): ID of the Google Cloud Platform project where the private
            cloud will be created.
        zone (str): zone where the private cloud will be created in the project
            identified by the `project_id`.
        network_name (str): name of the network to which the private cloud will
            be connected.
        cloud_name (str): name of the private cloud to be created, which is used
            to identify the created resource in the VMware Engine API.
        cluster_name (str): ID of a cluster to be created within the private cloud,
            which is required for proper configuration and management of nodes in
            the cloud.

    Returns:
        operation.Operation: an operation object containing the newly created
        private cloud.

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

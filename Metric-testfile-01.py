def _is_billing_enabled(project_name: str) -> bool:
    """
    Retrieves billing information for a specified Google Cloud Platform project
    and returns whether billing is enabled for that project.

    Args:
        project_name (str): name of the Google Cloud Platform project for which
            the billing status is to be retrieved.

    Returns:
        bool: a boolean value indicating whether billing is enabled for the specified
        project.

    """
    request = billing.GetProjectBillingInfoRequest(name=project_name)
    project_billing_info = cloud_billing_client.get_project_billing_info(request)

    return project_billing_info.billing_enabled


def _disable_billing_for_project(project_name: str) -> None:
  
    """
    Disables billing for a specified project by updating its billing information
    using the Cloud Billing API.

    Args:
        project_name (str): name of the project whose billing will be disabled.

    """
    request = billing.UpdateProjectBillingInfoRequest(
        name=project_name,
        project_billing_info=billing.ProjectBillingInfo(
            billing_account_name=""  # Disable billing
        ),
    )
    project_biling_info = cloud_billing_client.update_project_billing_info(request)
    print(f"Billing disabled: {project_biling_info}")


def create_container_job(project_id: str, region: str, job_name: str) -> batch_v1.Job:
   
    """
    Creates a job for running a containerized task, defines resources and allocation
    policy, and creates the job in a specified region.

    Args:
        project_id (str): Google Cloud Platform project that will contain the job.
        region (str): location where the job will be created and executed, and is
            used to specify the parent of the job in the CreateJobRequest.
        job_name (str): name of the job to be created, which is used as the value
            of the `job.id` field in the response.

    Returns:
        batch_v1.Job: a `batch_v1.Job` object representing the created job.

    """
    client = batch_v1.BatchServiceClient()

    # Define what will be done as part of the job.
    runnable = batch_v1.Runnable()
    runnable.container = batch_v1.Runnable.Container()
    runnable.container.image_uri = "gcr.io/google-containers/busybox"
    runnable.container.entrypoint = "/bin/sh"
    runnable.container.commands = [
        "-c",
        "echo Hello world! This is task ${BATCH_TASK_INDEX}. This job has a total of ${BATCH_TASK_COUNT} tasks.",
    ]

    # Jobs can be divided into tasks. In this case, we have only one task.
    task = batch_v1.TaskSpec()
    task.runnables = [runnable]

    # We can specify what resources are requested by each task.
    resources = batch_v1.ComputeResource()
    resources.cpu_milli = 2000  # in milliseconds per cpu-second. This means the task requires 2 whole CPUs.
    resources.memory_mib = 16  # in MiB
    task.compute_resource = resources

    task.max_retry_count = 2
    task.max_run_duration = "3600s"

    # Tasks are grouped inside a job using TaskGroups.
    # Currently, it's possible to have only one task group.
    group = batch_v1.TaskGroup()
    group.task_count = 4
    group.task_spec = task

    # Policies are used to define on what kind of virtual machines the tasks will run on.
    # In this case, we tell the system to use "e2-standard-4" machine type.
    # Read more about machine types here: https://cloud.google.com/compute/docs/machine-types
    policy = batch_v1.AllocationPolicy.InstancePolicy()
    policy.machine_type = "e2-standard-4"
    instances = batch_v1.AllocationPolicy.InstancePolicyOrTemplate()
    instances.policy = policy
    allocation_policy = batch_v1.AllocationPolicy()
    allocation_policy.instances = [instances]

    job = batch_v1.Job()
    job.task_groups = [group]
    job.allocation_policy = allocation_policy
    job.labels = {"env": "testing", "type": "container"}
    # We use Cloud Logging as it's an out of the box available option
    job.logs_policy = batch_v1.LogsPolicy()
    job.logs_policy.destination = batch_v1.LogsPolicy.Destination.CLOUD_LOGGING

    create_request = batch_v1.CreateJobRequest()
    create_request.job = job
    create_request.job_id = job_name
    # The job's parent is the region in which the job will run
    create_request.parent = f"projects/{project_id}/locations/{region}"

    return client.create_job(create_request)

def create_script_job_with_bucket(
    project_id: str, region: str, job_name: str, bucket_name: str) -> batch_v1.Job:
     
    """
    Creates a new job in Google Cloud Platform's Batch Engine using a script as
    the job's primary task, executing on a virtual machine with specific CPU and
    memory resources, and logs sent to Cloud Logging.

    Args:
        project_id (str): project ID where the job will run.
        region (str): Google Cloud Platform region where the job will be created
            and executed, which is used to determine the job's parent resource in
            the create_job method call.
        job_name (str): name of the job to be created.
        bucket_name (str): name of a Google Cloud Storage bucket where the script
            will be executed.

    Returns:
        batch_v1.Job: a batch job with a script that runs a command and saves the
        output to a Google bucket.

    """
    
    client = batch_v1.BatchServiceClient()

    # Define what will be done as part of the job.
    task = batch_v1.TaskSpec()
    runnable = batch_v1.Runnable()
    runnable.script = batch_v1.Runnable.Script()
    runnable.script.text = "echo Hello world from task ${BATCH_TASK_INDEX}. >> /mnt/share/output_task_${BATCH_TASK_INDEX}.txt"
    task.runnables = [runnable]

    gcs_bucket = batch_v1.GCS()
    gcs_bucket.remote_path = bucket_name
    gcs_volume = batch_v1.Volume()
    gcs_volume.gcs = gcs_bucket
    gcs_volume.mount_path = "/mnt/share"
    task.volumes = [gcs_volume]

    # We can specify what resources are requested by each task.
    resources = batch_v1.ComputeResource()
    resources.cpu_milli = 500  # in milliseconds per cpu-second. This means the task requires 50% of a single CPUs.
    resources.memory_mib = 16
    task.compute_resource = resources

    task.max_retry_count = 2
    task.max_run_duration = "3600s"

    # Tasks are grouped inside a job using TaskGroups.
    # Currently, it's possible to have only one task group.
    group = batch_v1.TaskGroup()
    group.task_count = 4
    group.task_spec = task

    # Policies are used to define on what kind of virtual machines the tasks will run on.
    # In this case, we tell the system to use "e2-standard-4" machine type.
    # Read more about machine types here: https://cloud.google.com/compute/docs/machine-types
    allocation_policy = batch_v1.AllocationPolicy()
    policy = batch_v1.AllocationPolicy.InstancePolicy()
    policy.machine_type = "e2-standard-4"
    instances = batch_v1.AllocationPolicy.InstancePolicyOrTemplate()
    instances.policy = policy
    allocation_policy.instances = [instances]

    job = batch_v1.Job()
    job.task_groups = [group]
    job.allocation_policy = allocation_policy
    job.labels = {"env": "testing", "type": "script", "mount": "bucket"}
    # We use Cloud Logging as it's an out of the box available option
    job.logs_policy = batch_v1.LogsPolicy()
    job.logs_policy.destination = batch_v1.LogsPolicy.Destination.CLOUD_LOGGING

    create_request = batch_v1.CreateJobRequest()
    create_request.job = job
    create_request.job_id = job_name
    # The job's parent is the region in which the job will run
    create_request.parent = f"projects/{project_id}/locations/{region}"

    return client.create_job(create_request)


def create_script_job(project_id: str, region: str, job_name: str) -> batch_v1.Job:
        
    """
    Creates a new job in Google Cloud Batch using the `batch v1` API, defining the
    task, resource requirements, and allocation policy, and logs policy, then
    creating the job with specified name and parent region.

    Args:
        project_id (str): Google Cloud Platform project that the job will be created
            in.
        region (str): Google Cloud Platform region where the job will run.
        job_name (str): 10-20 character name of the job to be created, which serves
            as an identifier for the job in the Cloud Platform.

    Returns:
        batch_v1.Job: a `batch v1.Job` resource.

    """
    client = batch_v1.BatchServiceClient()

    # Define what will be done as part of the job.
    task = batch_v1.TaskSpec()
    runnable = batch_v1.Runnable()
    runnable.script = batch_v1.Runnable.Script()
    runnable.script.text = "echo Hello world! This is task ${BATCH_TASK_INDEX}. This job has a total of ${BATCH_TASK_COUNT} tasks."
    # You can also run a script from a file. Just remember, that needs to be a script that's
    # already on the VM that will be running the job. Using runnable.script.text and runnable.script.path is mutually
    # exclusive.
    # runnable.script.path = '/tmp/test.sh'
    task.runnables = [runnable]

    # We can specify what resources are requested by each task.
    resources = batch_v1.ComputeResource()
    resources.cpu_milli = 2000  # in milliseconds per cpu-second. This means the task requires 2 whole CPUs.
    resources.memory_mib = 16
    task.compute_resource = resources

    task.max_retry_count = 2
    task.max_run_duration = "3600s"

    # Tasks are grouped inside a job using TaskGroups.
    # Currently, it's possible to have only one task group.
    group = batch_v1.TaskGroup()
    group.task_count = 4
    group.task_spec = task

    # Policies are used to define on what kind of virtual machines the tasks will run on.
    # In this case, we tell the system to use "e2-standard-4" machine type.
    # Read more about machine types here: https://cloud.google.com/compute/docs/machine-types
    allocation_policy = batch_v1.AllocationPolicy()
    policy = batch_v1.AllocationPolicy.InstancePolicy()
    policy.machine_type = "e2-standard-4"
    instances = batch_v1.AllocationPolicy.InstancePolicyOrTemplate()
    instances.policy = policy
    allocation_policy.instances = [instances]

    job = batch_v1.Job()
    job.task_groups = [group]
    job.allocation_policy = allocation_policy
    job.labels = {"env": "testing", "type": "script"}
    # We use Cloud Logging as it's an out of the box available option
    job.logs_policy = batch_v1.LogsPolicy()
    job.logs_policy.destination = batch_v1.LogsPolicy.Destination.CLOUD_LOGGING

    create_request = batch_v1.CreateJobRequest()
    create_request.job = job
    create_request.job_id = job_name
    # The job's parent is the region in which the job will run
    create_request.parent = f"projects/{project_id}/locations/{region}"

    return client.create_job(create_request)


def create_script_job_with_template(
    project_id: str, region: str, job_name: str, template_link: str
) -> batch_v1.Job:

    """
    Creates a Batch job with a script runnable, specifying resources, task group,
    allocation policy, and logs policy. It also defines the job's parent location
    and returns the created job object.

    Args:
        project_id (str): identifier of the Google Cloud Platform project in which
            the job will be created and executed.
        region (str): parent location of the job in the Batch Service API, which
            specifies the region where the job will be created and run.
        job_name (str): name of the job to be created, which is used as the value
            of the `parent` input parameter and is also the job's ID.
        template_link (str): link to an instance template that defines all the
            required parameters for the tasks in the job.

    Returns:
        batch_v1.Job: a `batch_v1.Job` object representing the created job.

    """
    client = batch_v1.BatchServiceClient()

    # Define what will be done as part of the job.
    task = batch_v1.TaskSpec()
    runnable = batch_v1.Runnable()
    runnable.script = batch_v1.Runnable.Script()
    runnable.script.text = "echo Hello world! This is task ${BATCH_TASK_INDEX}. This job has a total of ${BATCH_TASK_COUNT} tasks."
    # You can also run a script from a file. Just remember, that needs to be a script that's
    # already on the VM that will be running the job. Using runnable.script.text and runnable.script.path is mutually
    # exclusive.
    # runnable.script.path = '/tmp/test.sh'
    task.runnables = [runnable]

    # We can specify what resources are requested by each task.
    resources = batch_v1.ComputeResource()
    resources.cpu_milli = 2000  # in milliseconds per cpu-second. This means the task requires 2 whole CPUs.
    resources.memory_mib = 16
    task.compute_resource = resources

    task.max_retry_count = 2
    task.max_run_duration = "3600s"

    # Tasks are grouped inside a job using TaskGroups.
    # Currently, it's possible to have only one task group.
    group = batch_v1.TaskGroup()
    group.task_count = 4
    group.task_spec = task

    # Policies are used to define on what kind of virtual machines the tasks will run on.
    # In this case, we tell the system to use an instance template that defines all the
    # required parameters.
    allocation_policy = batch_v1.AllocationPolicy()
    instances = batch_v1.AllocationPolicy.InstancePolicyOrTemplate()
    instances.instance_template = template_link
    allocation_policy.instances = [instances]

    job = batch_v1.Job()
    job.task_groups = [group]
    job.allocation_policy = allocation_policy
    job.labels = {"env": "testing", "type": "script"}
    # We use Cloud Logging as it's an out of the box available option
    job.logs_policy = batch_v1.LogsPolicy()
    job.logs_policy.destination = batch_v1.LogsPolicy.Destination.CLOUD_LOGGING

    create_request = batch_v1.CreateJobRequest()
    create_request.job = job
    create_request.job_id = job_name
    # The job's parent is the region in which the job will run
    create_request.parent = f"projects/{project_id}/locations/{region}"

    return client.create_job(create_request)

def delete_job(project_id: str, region: str, job_name: str) -> Operation:
   
    """
    Deletes a job from Google Cloud Billing based on its name, specified in input
    parameters as a full URL. It returns an operation object containing information
    about the deleted job.

    Args:
        project_id (str): ID of the Google Cloud project where the job to be deleted
            is located and is used as a part of the API call to specify the job
            to be deleted.
        region (str): location where the job to be deleted is running and is used
            in the delete job API call to specify the job to be deleted.
        job_name (str): name of the job to be deleted, and it is used in the delete
            job API call to specify the job to be deleted.

    Returns:
        Operation: an `Operation` object containing information about the deleted
        job.

    """
    client = batch_v1.BatchServiceClient()

    return client.delete_job(
        name=f"projects/{project_id}/locations/{region}/jobs/{job_name}"
    )

def get_job(project_id: str, region: str, job_name: str) -> batch_v1.Job:
    """
    Retrieves a batch job from the Google Cloud Batch Service Client using the
    given project ID, region, and job name. It returns a `batch_v1.Job` object
    representing the specified job.

    Args:
        project_id (str): identifier of a Google Cloud Project in which the Job
            to be retrieved is located.
        region (str): location of the job to be retrieved from the Batch API, and
            is used as the value for the `name` field in the `get_job` method to
            identify the specific job to retrieve.
        job_name (str): identifier of the specific job to be retrieved from the
            Batch API.

    Returns:
        batch_v1.Job: a `batch_v1.Job` object representing the specified job.

    """
    client = batch_v1.BatchServiceClient()

    return client.get_job(
        name=f"projects/{project_id}/locations/{region}/jobs/{job_name}"
    )

def get_task(
    project_id: str, region: str, job_name: str, group_name: str, task_number: int) -> batch_v1.Task:
    """
    Retrieves a specific task from a Google Cloud batch queue using its project
    ID, region, job name, group name, and task number.

    Args:
        project_id (str): ID of a Google Cloud project required to identify and
            retrieve a specific task from a batch queue.
        region (str): location where the job associated with the task is being
            executed, which is required for Batch ServiceClient to locate the
            desired task.
        job_name (str): name of the job for which the task is to be retrieved.
        group_name (str): name of the task group that contains the specific task
            to be retrieved.
        task_number (int): 10-digit ID number of the specific task within the job's
            task group that the function will retrieve.

    Returns:
        batch_v1.Task: a `batch_v1.Task` object.

    """
    client = batch_v1.BatchServiceClient()

    return client.get_task(
        name=f"projects/{project_id}/locations/{region}/jobs/{job_name}"
        f"/taskGroups/{group_name}/tasks/{task_number}"
    )


def list_jobs(project_id: str, region: str) -> Iterable[batch_v1.Job]:
    """
    Retrieves a list of jobs from Google Cloud Batch service using a specified
    project ID and region, returning an iterable of `batch_v1.Job` objects.

    Args:
        project_id (str): ID of the project for which job information is requested.
        region (str): location where the jobs will be listed, and it is passed as
            a string value to the `list_jobs()` method of the Batch Service Client.

    Returns:
        Iterable[batch_v1.Job]: an iterable of `batch_v1.Job` objects representing
        jobs associated with a given project and region.

    """
    client = batch_v1.BatchServiceClient()

    return client.list_jobs(parent=f"projects/{project_id}/locations/{region}")
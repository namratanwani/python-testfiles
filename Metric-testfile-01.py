def _is_billing_enabled(project_name: str) -> bool:
    request = billing.GetProjectBillingInfoRequest(name=project_name)
    project_billing_info = cloud_billing_client.get_project_billing_info(request)

    return project_billing_info.billing_enabled


def _disable_billing_for_project(project_name: str) -> None:
  
    request = billing.UpdateProjectBillingInfoRequest(
        name=project_name,
        project_billing_info=billing.ProjectBillingInfo(
            billing_account_name=""  # Disable billing
        ),
    )
    project_biling_info = cloud_billing_client.update_project_billing_info(request)
    print(f"Billing disabled: {project_biling_info}")


def create_container_job(project_id: str, region: str, job_name: str) -> batch_v1.Job:
   
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

def create_script_job(project_id: str, region: str, job_name: str) -> batch_v1.Job:
    
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



def create_script_job(project_id: str, region: str, job_name: str) -> batch_v1.Job:
        
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
   
    client = batch_v1.BatchServiceClient()

    return client.delete_job(
        name=f"projects/{project_id}/locations/{region}/jobs/{job_name}"
    )

def get_job(project_id: str, region: str, job_name: str) -> batch_v1.Job:
    client = batch_v1.BatchServiceClient()

    return client.get_job(
        name=f"projects/{project_id}/locations/{region}/jobs/{job_name}"
    )

def get_task(
    project_id: str, region: str, job_name: str, group_name: str, task_number: int) -> batch_v1.Task:
    client = batch_v1.BatchServiceClient()

    return client.get_task(
        name=f"projects/{project_id}/locations/{region}/jobs/{job_name}"
        f"/taskGroups/{group_name}/tasks/{task_number}"
    )


def list_jobs(project_id: str, region: str) -> Iterable[batch_v1.Job]:
    client = batch_v1.BatchServiceClient()

    return client.list_jobs(parent=f"projects/{project_id}/locations/{region}")
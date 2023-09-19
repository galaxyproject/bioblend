from bioblend.galaxy import GalaxyInstance


def get_inputs(server, api_key, workflow_name, session=None):
    """
    Function to get an array of inputs for a given galaxy workflow

    Usage:
        get_inputs(
            server = "galaxy.server.org",
            api_key = "user_api_key",
            workflow_name = "workflow_name",
        )

    Args:
        server (string): Galaxy server address
        api_key (string): User generated string from galaxy instance
            to create: User > Preferences > Manage API Key > Create a new key
        workflow_name (string): Target workflow name
    Returns:
        inputs (array of strings): Input files expected by the workflow, these will be in the same order as they should be given in the main API call
    """

    gi = GalaxyInstance(url=server, key=api_key, session=session)
    api_workflow = gi.workflows.get_workflows(name=workflow_name)
    steps = gi.workflows.export_workflow_dict(api_workflow[0]["id"])["steps"]
    inputs = []
    for step in steps:
        # Some of the steps don't take inputs so have to skip these
        if len(steps[step]["inputs"]) > 0:
            inputs.append(steps[step]["inputs"][0]["name"])

    return inputs


def get_workflows(server, api_key, session=None):
    """
    Function to get an array of workflows available on a given galaxy instance

    Usage:
        get_workflows(
            server = "galaxy.server.org",
            api_key = "user_api_key",
        )

    Args:
        server (string): Galaxy server address
        api_key (string): User generated string from galaxy instance
            to create: User > Preferences > Manage API Key > Create a new key
    Returns:
        workflows (array of strings): Workflows available to be run on the galaxy instance provided
    """
    gi = GalaxyInstance(url=server, key=api_key, session=session)
    workflows_dict = gi.workflows.get_workflows()
    workflows = []
    for item in workflows_dict:
        workflows.append(item["name"])
    return workflows

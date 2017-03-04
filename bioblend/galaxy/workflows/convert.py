
import json
import uuid

from collections import OrderedDict


STEP_TYPE_ALIASES = {
    'input': 'data_input',
    'input_collection': 'data_collection_input',
}

def uniquify(name, taken):
    if name not in taken:
        return name

    while True:
        res = re.search(r'^(.*)_(\d+)$', name)
        if res:
            name = "%s_%s" % (res.group(1), int(res.group(2)) + 1)
        else:
            name = "%s_1" % (name)
        if name not in taken:
            return name

def workflow_to_simple(workflow):
    """
    convert a galaxy formatted workflow to a 'simple'
    format that is more human friendly to read
    """

    steps = workflow['steps']

    step_map = {}
    steps_out = []
    for step_id, step in steps.items():
        label = step.get("label", "step_%s" % (step_id))
        label = uniquify(label, step_map)
        step_map[step_id] = label

    for step_id, step in steps.items():
        new_step = {
            'label' : step_map[step_id]
        }
        if step['type'] == 'data_input':
            new_step['type'] = 'input'
        if step['type'] == 'pause':
            new_step['type'] = 'pause'
        if step['type'] == 'tool':
            new_step['tool_id'] = step['tool_id']
            state = json.loads(step['tool_state'])
            new_state = {}
            for k,v in state.items():
                if k not in ['__page__', '__rerun_remap_job_id__']:
                    new_v = json.loads(v)
                    if new_v is not None:
                        new_state[k] = new_v
            new_step['state'] = new_state
            connections = {}
            for connection_name, connection in step['input_connections'].items():
                connections[connection_name] = step_map[str(connection['id'])] + "#" + connection['output_name']
            if len(connections):
                new_step['connect'] = connections
        steps_out.append(new_step)

    out = {}
    out['name'] = workflow['name']
    out['uuid'] = workflow.get('uuid', str(uuid.uuid4()))
    out['steps'] = steps_out

    return out


def simple_to_workflow(simple_workflow):
    """
    Convert a workflow stored in the 'simple' human friendly
    format to a galaxy compatible structure
    """

    if isinstance(simple_workflow, list):
        simple_workflow = {"steps": simple_workflow}

    __ensure_defaults(simple_workflow, {
        "a_galaxy_workflow": "true",
        "format-version": "0.1",
        "annotation": "",
        "name": "Workflow",
        "uuid": str(uuid.uuid4()),
    })

    steps = simple_workflow["steps"]

    conversion_context = ConversionContext()
    if isinstance(steps, list):
        steps_as_dict = OrderedDict()
        for i, step in enumerate(steps):
            steps_as_dict[ str(i) ] = step
            if "id" not in step:
                step["id"] = i

            if "label" in step:
                label = step["label"]
                conversion_context.labels[label] = i

            if "position" not in step:
                # TODO: this really should be optional in Galaxy API.
                step["position"] = {
                    "left": 10 * i,
                    "top": 10 * i
                }

        simple_workflow["steps"] = steps_as_dict
        steps = steps_as_dict

    for i, step in steps.iteritems():
        step_type = step.get("type", "tool")
        step_type = STEP_TYPE_ALIASES.get(step_type, step_type)
        if step_type not in [ "data_input", "data_collection_input", "tool", "pause"]:
            raise Exception("Unknown step type encountered %s" % step_type)
        step["type"] = step_type
        eval("transform_%s" % step_type)(conversion_context, step)

    return simple_workflow


def transform_data_input(context, step):
    transform_input(context, step, default_name="Input dataset")


def transform_data_collection_input(context, step):
    transform_input(context, step, default_name="Input dataset collection")


def transform_input(context, step, default_name):
    default_name = step.get("label", default_name)
    __ensure_defaults( step, {
        "annotation": "",
    })

    __ensure_inputs_connections(step)

    if not "inputs" in step:
        step["inputs"] = [{}]

    step_inputs = step["inputs"][0]
    if "name" in step_inputs:
        name = step_inputs["name"]
    else:
        name = default_name

    __ensure_defaults( step_inputs, {
        "name": name,
        "description": "",
    })
    tool_state = {
        "name": name
    }
    if "collection_type" in step:
        tool_state["collection_type"] = step["collection_type"]

    __populate_tool_state(step, tool_state)


def transform_pause(context, step, default_name="Pause for dataset review"):
    default_name = step.get("label", default_name)
    __ensure_defaults( step, {
        "annotation": "",
    })

    __ensure_inputs_connections(step)

    if not "inputs" in step:
        step["inputs"] = [{}]

    step_inputs = step["inputs"][0]
    if "name" in step_inputs:
        name = step_inputs["name"]
    else:
        name = default_name

    __ensure_defaults( step_inputs, {
        "name": name,
    })
    tool_state = {
        "name": name
    }

    connect = __init_connect_dict(step)
    __populate_input_connections(context, step, connect)
    __populate_tool_state(step, tool_state)


def transform_tool(context, step):
    if "tool_id" not in step:
        raise Exception("Tool steps must define a tool_id.")

    __ensure_defaults( step, {
        "annotation": "",
        "post_job_actions": {},
    } )
    post_job_actions = step["post_job_actions"]

    tool_state = {
        # TODO: Galaxy should not require tool state actually specify a __page__.
        "__page__": 0,
    }

    connect = __init_connect_dict(step)

    def append_link(key, value):
        if key not in connect:
            connect[key] = []
        connect[key].append(value["$link"])

    def replace_links(value, key=""):
        if __is_link(value):
            append_link(key, value)
            return None
        if isinstance(value, dict):
            new_values = {}
            for k, v in value.iteritems():
                new_key = __join_prefix(key, k)
                new_values[k] = replace_links(v, new_key)
            return new_values
        elif isinstance(value, list):
            new_values = []
            for i, v in enumerate(value):
                # If we are a repeat we need to modify the key
                # but not if values are actually $links.
                if __is_link(v):
                    append_link(key, v)
                    new_values.append(None)
                else:
                    new_key = "%s_%d" % ( key, i )
                    new_values.append(replace_links(v, new_key))
            return new_values
        else:
            return value

    if "state" in step:
        step_state = step["state"]
        step_state = replace_links(step_state)

        for key, value in step_state.iteritems():
            tool_state[key] = json.dumps(value)
        del step["state"]

    # Fill in input connections
    __populate_input_connections(context, step, connect)

    __populate_tool_state(step, tool_state)

    # Handle outputs.
    if "outputs" in step:
        for name, output in step.get("outputs", {}).items():
            if output.get("hide", False):
                action_name = "HideDatasetAction%s" % name
                action = __action(
                    "HideDatasetAction",
                    name,
                )
                post_job_actions[action_name] = action

            if output.get("rename", None):
                new_name = output.get("rename")
                action_name = "RenameDatasetAction%s" % name
                arguments = dict(newname=new_name)
                action = __action(
                    "RenameDatasetAction",
                    name,
                    arguments,
                )
                post_job_actions[action_name] = action

        del step["outputs"]


class ConversionContext(object):

    def __init__(self):
        self.labels = {}


def __action(type, name, arguments={}):
    return {
        "action_arguments": arguments,
        "action_type": type,
        "output_name": name,
    }


def __is_link(value):
    return isinstance(value, dict) and "$link" in value


def __join_prefix(prefix, key):
    if prefix:
        new_key = "%s|%s" % (prefix, key)
    else:
        new_key = key
    return new_key


def __init_connect_dict(step):
    if "connect" not in step:
        step["connect"] = {}

    connect = step["connect"]
    del step["connect"]
    return connect


def __populate_input_connections(context, step, connect):
    __ensure_inputs_connections(step)
    input_connections = step["input_connections"]

    for key, values in connect.iteritems():
        input_connection_value = []
        if not isinstance(values, list):
            values = [ values ]
        for value in values:
            if not isinstance(value, dict):
                if key == "$step":
                    value += "#__NO_INPUT_OUTPUT_NAME__"
                value_parts = str(value).split("#")
                if len(value_parts) == 1:
                    value_parts.append("output")
                id = value_parts[0]
                if id in context.labels:
                    id = context.labels[id]
                value = {"id": int(id), "output_name": value_parts[1]}
            input_connection_value.append(value)
        if key == "$step":
            key = "__NO_INPUT_OUTPUT_NAME__"
        input_connections[key] = input_connection_value


def __ensure_inputs_connections(step):
    if "input_connections" not in step:
        step["input_connections"] = {}


def __ensure_defaults(in_dict, defaults):
    for key, value in defaults.items():
        if key not in in_dict:
            in_dict[ key ] = value


def __populate_tool_state(step, tool_state):
    step["tool_state"] = json.dumps(tool_state)

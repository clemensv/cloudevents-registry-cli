import json
import os
import urllib.request
import urllib.parse
import urllib.error
import yaml

schemas_handled = set()
current_url = ""

def add_schema_to_handled(url):
    global schemas_handled
    schemas_handled.add(url)

def reset_schemas_handled():
    global schemas_handled
    schemas_handled = set()

def get_current_url():
    global current_url
    return current_url

def set_current_url(url):
    global current_url
    current_url = url

def get_schemas_handled():
    global schemas_handled
    return schemas_handled

# Load the definition file, which may be a JSON Schema
# or CloudEvents message definition group. Since URLs
# found in documents may be redirected by their hosts,
# the function returns the actual URL as the first return
# value and the parsed object representing the document's
# information set
def load_definitions_core(definitions_file: str, headers: dict, ignore_handled: bool = False):
    docroot: dict = {}
    global current_url
    try:
        if definitions_file.startswith("http"):
            req = urllib.request.Request(definitions_file, headers=headers)
            with urllib.request.urlopen(req) as url:
                # URIs may redirect and we only want to handle each file once
                current_url = url.url
                parsed_url = urllib.parse.urlparse(url.url)
                definitions_file = urllib.parse.urlunparse(
                    parsed_url._replace(fragment=''))
                if not ignore_handled:
                    if definitions_file not in schemas_handled:
                        schemas_handled.add(definitions_file)
                    else:
                        return None, None
                textDoc = url.read().decode()
                try:
                    docroot = json.loads(textDoc)
                except json.decoder.JSONDecodeError as e:
                    try:
                        # if the JSON is invalid, try to parse it as YAML
                        docroot = yaml.safe_load(textDoc)
                    except yaml.YAMLError as e:
                        docroot = textDoc
        else:
            if not ignore_handled:
                if definitions_file not in schemas_handled:
                    schemas_handled.add(definitions_file)
                else:
                    return None, None
            with open(os.path.join(os.getcwd(), definitions_file), "r") as f:
                textDoc = f.read()
                try:
                    docroot = json.loads(textDoc)
                except json.decoder.JSONDecodeError as e1:
                    try:
                        # if the JSON is invalid, try to parse it as YAML
                        docroot = yaml.safe_load(textDoc)
                    except yaml.YAMLError as e2:
                        raise e1
    except urllib.error.URLError as e:
        print("An error occurred while trying to open the URL: ", e)
        return None, None
    except json.decoder.JSONDecodeError as e:
        print("An error occurred while trying to parse the JSON file: ", e)
        return None, None
    except IOError as e:
        print("An error occurred while trying to access the file: ", e)
        return None, None

    return definitions_file, docroot


def load_definitions(definitions_file: str, headers: dict, load_schema: bool = False, ignore_handled: bool = False):
    # for a CloudEvents message definition group, we
    # normalize the document to be a messagegroups doc
    definitions_file, docroot = load_definitions_core(definitions_file, 
                                                      headers, ignore_handled)
    
    if docroot is None:
        return None, None

    if load_schema:
        return definitions_file, docroot

    # if "$schema" in docroot:
    #     if docroot["$schema"] != "https://cloudevents.io/schemas/registry":
    #         print("unsupported schema:" + docroot["$schema"])
    #         return None, None
    if "messagegroupsurl" in docroot:
        _, subroot = load_definitions_core(docroot["messagegroupsurl"], 
                                           headers)
        docroot["messagegroups"] = subroot
        docroot["messagegroupsurl"] = None
    if "schemagroupsUrl" in docroot:
        _, subroot = load_definitions_core(docroot["schemagroupsurl"], 
                                           headers)
        docroot["schemagroups"] = subroot
        docroot["schemagroupsurl"] = None
    if "endpointsUrl" in docroot:
        _, subroot = load_definitions_core(docroot["endpointsurl"], 
                                           headers)
        docroot["endpoints"] = subroot
        docroot["endpointsurl"] = None

    # make sure the document is always of the same form, even if
    # the URL was a deep link. We can drill to the level of an
    # endpoint, a definitiongroup, or a schemagroup
    newroot = {"$schema": "https://cloudevents.io/schemas/registry"}

    # the doc is an dict
    if isinstance(docroot, dict) and "type" in docroot[list(
            docroot.keys())[0]]:
        dictentry = docroot[list(docroot.keys())[0]]
        if dictentry["type"] == "definitiongroup":
            newroot["messagegroups"] = docroot
        elif dictentry["type"] == "schemagroup":
            newroot["schemagroups"] = docroot
        elif dictentry["type"] == "endpoint":
            newroot["endpoints"] = docroot
        else:
            print("unknown doc structure")
            return None, None
        docroot = newroot

    # the doc is an object
    elif "type" in docroot:
        if docroot["type"] == "definitiongroup":
            newroot["messagegroups"] = {docroot["id"]: docroot}
        elif docroot["type"] == "schemagroup":
            newroot["schemagroups"] = {docroot["id"]: docroot}
        elif docroot["type"] == "endpoints":
            newroot["endpoints"] = {docroot["id"]: docroot}
        else:
            print("unknown type:" + docroot["type"])
            return None, None
        docroot = newroot

    return definitions_file, docroot

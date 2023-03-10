import argparse

from .commands.validate_definitions import validate_definition
from .commands.generate_code import generate_code
from .commands.list_templates import list_templates, enum_templates

# delay output for the generator choices until we actually need them
class TemplateChoicesHelpFormatter(argparse.HelpFormatter):

    def _format_text(self, text):
        if text == "...":
            return "Generate code from a definition file based on a template set (style).\n\nBuilt-in choices for --language/--style:\n\n"+ "\n ".join(enum_templates())
        return argparse.RawDescriptionHelpFormatter._format_text(self, text)

def main():
   
    # Create an ArgumentParser object
    parser = argparse.ArgumentParser()
    
    # the script accepts a set of commands, each with its own set of arguments
    # the first argument is the command name:
    #  generate: generates code from input definitions
    #  validate: validates an definition
    #  list: lists the available templates

    subparsers = parser.add_subparsers(dest="command", help="The command to execute: generate, validate or list")
    subparsers.default = "generate"
    generate = subparsers.add_parser("generate", help="Generate code.", epilog="...", formatter_class=TemplateChoicesHelpFormatter) 
    generate.set_defaults(func=generate_code)
    validate = subparsers.add_parser("validate", help="Validate a definition")
    validate.set_defaults(func=validate_definition)
    list1 = subparsers.add_parser("list", help="List available templates")
    list1.set_defaults(func=list_templates)
    subparsers.required = True
    
    # Specify the arguments for the generate command
    generate.add_argument("--projectname", dest="project_name", required=True, help="The project name (namespace name) for the output")
    generate.add_argument("--schemaprojectname", dest="schema_project_name", required=False, help="The project name (namespace name) for schema classes (optional, defaults to projectname)")
    generate.add_argument("--noschema", dest="no_schema", action="store_true", required=False, help="Do not generate schema classes (optional, defaults to false)")
    generate.add_argument("--nocode", dest="no_code", action="store_true", required=False, help="Do not generate non-schema code like consumers or producers (optional, defaults to false)")
    generate.add_argument("--language", dest="language", required=True, help="The language to use for the generated code")
    generate.add_argument("--style", dest="style", required=True, help="The style of the generated code")
    generate.add_argument("--output", dest="output_dir", required=True, help="The directory where the generated code should be saved")
    generate.add_argument("--definitions", dest="definitions_file", required=True, help="The file or URL containing the definitions")
    generate.add_argument("--requestheaders", nargs="*", dest="headers", required=False,help="Extra HTTP headers in the format 'key=value'")
    generate.add_argument("--templates", nargs="*", dest="template_dirs", required=False, help="Paths of extra directories containing custom templates")
    generate.add_argument("--template-args", nargs="*", dest="template_args", required=False, help="Extra template arguments to pass to the code generator in the form 'key=value")
    
    # specify the arguments for the validate command
    validate.add_argument("--definitions", dest="definitions_file", required=True, help="The file or URL containing the definitions")
    validate.add_argument("--requestheaders", nargs="*", dest="headers", required=False,help="Extra HTTP headers in the format 'key=value'")

    # specify the arguments for the list command
    list1.add_argument("--templates", nargs="*", dest="template_dirs", required=False, help="Paths of extra directories containing custom templates")
    list1.add_argument("--format", dest="listformat", required=False, help="Format for the output: text or json", choices=["text", "json"], default="text")
    
        
    # Parse the command line arguments
    args = parser.parse_args()
    return args.func(args)    

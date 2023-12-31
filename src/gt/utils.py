import sys, os, os.path, re, shutil, subprocess
from . import *
from typing import Dict, List


class SourceFile:
    def __init__(self, *, name: str, project: str, language: str, src_type: str="main") -> None:
        self.name     = name
        self.project  = project
        self.language = language
        self.src_type = src_type # "test" or "main"

    def directory(self) -> str:
        return os.path.join(PROJECTS[self.project], os.sep.join(["src", self.src_type, self.language]))

    def path(self) -> str:
        return os.path.join(self.directory(), f"{self.name}.{SourceFile.get_extension(self.language)}")

    def exists(self) -> bool:
        return os.path.isfile(self.path())

    def create(self) -> None:
        pth = self.path()
        dir = self.directory()
        if not os.path.exists(pth):
            ensure_dirs_exist(directories=dir)
            open(self.path(), "w").close()
            print(f"✔ Created {pth}")
        else:
            print(f"✘ Skipped {pth}")

    def remove(self) -> None:
        pth = self.path()
        if self.exists():
            os.remove(pth)
            print(f"󰆴 Removed {pth}")
        else:
            print(f"✘ Skipped {pth}")

    @staticmethod
    def create_all(files: List["SourceFile"]) -> None:
        for file in files:
            file.create()

    @staticmethod
    def remove_all(files: List["SourceFile"]) -> None:
        for file in files:
            file.remove()

    @staticmethod
    def get_extension(language: str):
        if language == "java":
            return "java"
        elif language == "cpp":
            return "cpp"
        elif language == "kotlin":
            return "kt"


class Package:
    def __init__(self, *, name: str, project: str, language: str, src_type: str) -> None:
        self.name       = name # can be fully qualified e.g: example.package
        self.project = project
        self.src_type   = src_type
        self.language   = language

    def name_to_rel_path(self) -> str:
        return self.name.replace(".", os.sep)

    def rel_path(self) -> str:
        head = os.sep.join(["src", self.src_type, self.language])
        tail = self.name_to_rel_path()
        return os.path.join(head, tail)

    def path(self) -> str:
        return os.path.join(PROJECTS[self.project], self.rel_path())

    def exists(self) -> bool:
        return os.path.isdir(self.path())

    def create(self) -> None:
        path = self.path()
        if os.path.exists(path):
            print(f"✘ Skipped package '{self.name}' in the {self.src_type} source tree of '{self.project}'")
        else:
            os.makedirs(path)
            print(f"✔ Created package '{self.name}' in the {self.src_type} source tree of '{self.project}'")

    def remove(self) -> None:
        if self.exists():
            shutil.rmtree(self.path())            
            print(f"󰆴 Removed package '{self.name}' from the {self.src_type} source tree of '{self.project}'")
        else:
            print(f"✘ Skipped nonexistence package '{self.name}' in the {self.src_type} source tree of '{self.project}'")

    @staticmethod
    def create_all(packages: List["Package"]) -> None:
        for p in packages:
            p.create()

    @staticmethod
    def remove_all(packages: List["Package"]) -> None:
        for p in packages:
            p.remove()

    @staticmethod
    def ensure_exist(pkg: "Package") -> None:
        if not pkg.exists():
            raise Exception(f"The package {pkg.name} does not exist.")

    @staticmethod
    def validate_names(packages: List[str]) -> None:
        if not packages: # Nothing to do
            return
        for package in packages:
            if os.sep in package:
                raise Exception("Package names cannot contain path separators.")
            if str.isdigit(package[0]):
                raise Exception("Package names cannot begin with a digit.")


def ensure_sufficient_args(*, args: List[str], err_msg:str) -> None:
    if not args:
        raise Exception(err_msg)


def extract_and_validate_project_from_args(*, args: List[str]) -> str:
    if SINGLE_PROJECT_BUILD:
        project = os.path.basename(ROOT_PROJECT)
    else:
        project = args.pop(0)

    # Validate
    if project not in PROJECTS:
        raise Exception("'{}' is not a valid subproject".format(project))

    return project


def generate_subprojects(*, project_names: List[str], project_type: str=""):
    # Perform validation
    valid_subproject_names = []
    invalid_subproject_names = []
    for subproject in project_names:
        if subproject in PROJECTS:
            print(f"✘ Skipped existing subproject '{subproject}'")
        if is_valid_project_name(subproject):
            valid_subproject_names.append(subproject)
        else:
            invalid_subproject_names.append(subproject)

    if valid_subproject_names:
        # Set up the temp directory to run gradle init
        temp_dir = "/tmp/temp_gradle_project"
        temp_name = os.path.basename(ROOT_PROJECT)
        if os.path.exists(temp_dir):
            if os.path.isdir(temp_dir):
                shutil.rmtree(temp_dir)
            else:
                os.remove(temp_dir)
        os.makedirs(temp_dir)
        
        # Run gradle init from inside temp directory
        os.chdir(temp_dir)
        options = ["--no-split-project", "--package", f"{temp_name}", "--project-name", f"{temp_name}", "--type", f"{project_type}"]
        cmd = ["gradle", "init"] + options
        try:
            subprocess.run(cmd, stdout=sys.stdout, stdin=sys.stdin)
            print()

            # Identify the subproject directory in the newly initialized project
            # Usually, this directory is 'app'
            _, dirnames, _ = next(os.walk("."))
            temp_subproject = ""
            for dir in dirnames:
                if (os.path.isfile(f"{dir}/build.gradle") or
                    os.path.isfile(f"{dir}/build.gradle.kts")):
                    temp_subproject = dir
                    break

            # Create subproject by copying the temp project into the actual root project
            if temp_subproject:
                for subproject in valid_subproject_names:
                    dest = os.path.join(ROOT_PROJECT, f"{subproject}")
                    shutil.copytree(temp_subproject, dest)
                    print(f"✔ Created subproject '{subproject}' of type '{project_type}'")
                    include_subproject_in_settings_file(subproject)

            # Also copy libs.versions.toml into ROOT_PROJECT/gradle if it doesn't already exist
            libs_versions_toml_root = os.path.join(ROOT_PROJECT, "gradle/libs.versions.toml")
            if not os.path.isfile(libs_versions_toml_root):
                shutil.copy2("gradle/libs.versions.toml", libs_versions_toml_root)
        except KeyboardInterrupt:
            print()
            print("KeyboardInterrupt signal received.")
            print("No subprojects were created.")

    if invalid_subproject_names:
        print(f"The following are not valid subproject names: {', '.join(invalid_subproject_names)}")


def generate_springboot_subprojects(*, project_names: List[str], user_specified_parameters: Dict[str, str]) -> None:
    # Perform validation
    valid_subproject_names = []
    invalid_subproject_names = []
    for project in project_names:
        if project in PROJECTS:
            print(f"✘ Skipped existing subproject '{project}'")
        else:
            if is_valid_project_name(project):
                valid_subproject_names.append(project)
            else:
                invalid_subproject_names.append(project)

    # Generate subprojects
    for subproject_name in valid_subproject_names:
        # Opinionated defaults
        parameters_with_default_value: Dict[str, str] = {
            "applicationName": f"{str.upper(subproject_name[0]) + subproject_name[1:]}Application",
            "artifactId"     : subproject_name,
            "baseDir"        : subproject_name,
            "name"           : subproject_name,
            "packageName"    : subproject_name,
            "type"           : "gradle-project-kotlin",
        }
        
        parameter_string = "" 
        for param in user_specified_parameters:
            if param == "baseDir":
                # baseDir will be ignored regardless
                print("The '--baseDir' option provided will be ignored since "
                      "the baseDir is a subdirectory of the root project with"
                      "the same name as the subproject.")
            elif param == "type":
                if user_specified_parameters[param] not in ("gradle-project", "gradle-project-kotlin"):
                    print("Only gradle-style SpringBoot projects are supported. "
                          "The --type option provided will be ignored. The default "
                          "type (gradle-project-kotlin) will be used instead.")
                else:
                    parameters_with_default_value[param] = user_specified_parameters[param]
            else:
                if param in parameters_with_default_value:
                    parameters_with_default_value[param] = user_specified_parameters[param]
                else:
                    parameter_string += f"-d {param}={user_specified_parameters[param]} "
        
        # Also add the parameter with default values
        for param in parameters_with_default_value:
            parameter_string += f"-d {param}={parameters_with_default_value[param]} "

        # Generate a springboot project template using the SpringInitializr API
        cmd= f"curl -sG https://start.spring.io/starter.tgz {parameter_string} | tar -xzf -"
        os.chdir(ROOT_PROJECT)
        ret_val = os.popen(cmd)
        if ret_val.close(): # Should be None if subprocess exits without errors
            # An error occurred.
            print(f"✘ Failed to create SpringBoot subproject '{subproject_name}'")
        else:
            # Perform clean-up
            subproject_dir = os.path.join(ROOT_PROJECT, subproject_name)
            files_to_remove = ("settings.gradle.kts", "settings.gradle", "gradlew", "gradlew.bat", "gradle")
            for file in files_to_remove:
                path = os.path.join(subproject_dir, file)
                if os.path.isfile(path):
                    os.remove(path)
                elif os.path.isdir(path):
                    shutil.rmtree(path)
            print(f"✔ Created SpringBoot subproject '{subproject_name}'")
            include_subproject_in_settings_file(subproject_name)

    if invalid_subproject_names:
        print(f"The following are not valid subproject names: {', '.join(invalid_subproject_names)}")


def get_included_subprojects() -> List[str]:
    included_projects: List[str] = []
    include_patterns = (
        "include\((\"(?P<project>.+)\")\)", # Double quotes style
        "include\('(?P<project>.+)'\)" # Single quotes style
    )
    if SETTINGS_FILE:
        with open(SETTINGS_FILE, "r") as file:
            for line in file:
                for p in include_patterns:
                    m = re.search(p, line)
                    if m:
                        included_projects.append(m.group("project"))
                        break
    return included_projects


def include_subproject_in_settings_file(subproject: str) -> None:
    if subproject not in get_included_subprojects():
        with open(SETTINGS_FILE, "a") as file:
            include_statement = f"include(\"{subproject}\")\n"
            file.write(include_statement)


def language_resolver(arg: str) -> str:
    if arg in ("-", "all", "-a", "--all"):
        return "all"

    if arg in ("-j", "-jv", "-ja", "-java", "-jav", "-jva", "java", "jav", "ja"):
        return "java"

    if arg in ("-k", "-kt", "-kot", "-ktl", "-kotlin", "kt", "kot", "ktl", "kotlin"):
        return "kotlin"

    if arg in ("cpp"):
        return "cpp"

    return arg


def ensure_dirs_exist(*, directories: List[str] | str) -> None:
    # Create all the necessary directories if they don't already exist
    dirs_to_check = []
    if type(directories) == list:
        dirs_to_check.extend(directories)

    if type(directories) == str:
        dirs_to_check.append(directories)

    for d in dirs_to_check:
        if not os.path.isdir(d):
            os.makedirs(d)


def is_valid_project_name(name: str) -> bool:
    if ((os.sep in name) or
        ("." in name)    or
        name.startswith("-")):
        return False
    return True


def report_nonexisting_projects(projects: List[str]) -> None:
    if not projects:
        return

    quoted = [f"'{p}'" for p in projects]
    if len(quoted) > 1:
        be = "are"
        article = ""
        plural_modifier = "s"
    else:
        be = "is"
        article = " a"
        plural_modifier = ""
    print(f"{', '.join(quoted)} {be} not{article} valid subproject{plural_modifier}.")


def report_incomplete_or_missing_src_sets(projects: List[str], *, src_language: str) -> None:
    if not projects:
        return

    quoted = [f"'{p}'" for p in projects]
    if len(quoted) > 1:
        be = "are"
        plural_modifier = "s"
    else:
        be = "is"
        plural_modifier = ""
    print(f"The source set{plural_modifier} for the {src_language} language in {', '.join(quoted)} {be} incomplete/missing.")


def raise_unrecognized_opts_error(*, opts: List[str], cmd: str) -> None:
    if not opts:
        return
    quoted = [f"'{opt}'" for opt in opts]
    if len(quoted) > 1:
        be = "are"
        article = ""
        plural_modifier = "s"
    else:
        be = "is"
        article = " a"
        plural_modifier = ""
    raise Exception(f"{', '.join(quoted)} {be} not{article} valid option{plural_modifier} for '{cmd}'")


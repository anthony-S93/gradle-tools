import os.path, re
from typing import List, Tuple
from .. import *
from ..utils import *


class JavaSourceFile(SourceFile):
    # For java, each source file is associated with one public class
    def __init__(self, *, classname: str, project: str, src_type: str = "main") -> None:

        # Separate package and file names
        pkgname, classname = JavaPackage.split_qualified_classname(classname)

        # Make sure the classname follows Java rules
        JavaSourceFile.validate_classname(classname)
        
        # Initialization        
        super().__init__(name=classname, project=project, language="java", src_type=src_type)
        if not pkgname:
            self.package = None
        else:
            self.package = JavaPackage(pkgname=pkgname, project=self.project, src_type=self.src_type)

    def directory(self) -> str:
        rel_path = os.sep.join(["src", self.src_type, "java"])
        if self.package:
            rel_path = os.path.join(rel_path, self.package.name_to_rel_path())
        return os.path.join(PROJECTS[self.project], rel_path)

    def create(self) -> None:
        # The package needs to exist first before the file can be created
        super().create()

    @staticmethod
    def validate_classname(classname: str) -> None:
        if not classname:
            raise Exception("Class names cannot be empty.")

        # Class names cannot contain path separators
        if os.sep in classname:
            raise Exception("Class names cannot contain path separators.")

        # Class names cannot begin with a digit
        if str.isdigit(classname[0]):
            raise Exception("Class names cannot begin with a digit.")


class JavaPackage(Package):
    def __init__(self, *, pkgname: str, project: str, src_type: str) -> None:

        # Make sure the package name obeys Java rules
        JavaPackage.validate_name(pkgname)

        # Initialization
        super().__init__(name=pkgname, project=project, language="java", src_type=src_type)

    @staticmethod
    def split_qualified_classname(classname: str) -> Tuple[str, str]:
        # p1.p2.classname will yield ("p1.p2", "classname")
        components = classname.rsplit(".", 1)
        if len(components) == 1:
            # Default package
            return ("", components[0])
        return (components[0], components[1])

    @staticmethod
    def validate_name(pkgname: str) -> None:
        if not pkgname: # Nothing to do
            return
        components = pkgname.split(".")
        for name in components:
            if os.sep in name:
                raise Exception("Package names cannot contain path separators.")
            if "-" in name:
                raise Exception("Package names cannot contain hyphens.")
            if str.isdigit(name[0]):
                raise Exception("Package names cannot begin with a digit.")

# Command handlers
def _add_class(args: List[str]) -> None:
    ensure_sufficient_args(args=args,
                           err_msg="Usage: gt java add-class [project] [-t] [-p <package_prefix>] <classes>") 
    project = extract_and_validate_project_from_args(args=args)

    # Detect options and their arguments
    include_test_tree = False
    package_flag_present = False
    unrecognized_opts = set()
    prefix_package = ""
    while args:
        opt = args.pop(0)
        if opt.startswith("-"):
            if opt == "-t":
                include_test_tree = True
            elif opt == "-p":
                package_flag_present = True
                if args:
                    value = args.pop(0)
                    if not value.startswith("-"):
                        prefix_package = value
                    else:
                        args.insert(0, value)
            else:
                unrecognized_opts.add(opt)
        else:
            args.insert(0, opt)
            break
    
    if unrecognized_opts:
            raise_unrecognized_opts_error(opts=unrecognized_opts, cmd="gt java add-class")
    
    ensure_sufficient_args(args=args, err_msg="Please specify at least one class to create.")
    
    # The remaining arguments are assumed to be classnames
    main_classes = [classname for classname in args]
    
    if package_flag_present:
        if not prefix_package:
            raise Exception("The '-p' option must be followed by a package name.")
        
        # Append the prefix package to all provided classes
        main_classes = [".".join([prefix_package, classname]) for classname in main_classes]

    if include_test_tree:
        test_classes = [classname + "Test" for classname in main_classes]
    else:
        test_classes = []
    
    main_sources = [JavaSourceFile(classname=classname, project=project, src_type="main") for classname in main_classes]
    test_sources = [JavaSourceFile(classname=classname, project=project, src_type="test") for classname in test_classes]
    SourceFile.create_all(main_sources + test_sources)


def _add_testclass(args: List[str]) -> None:
    ensure_sufficient_args(args=args,
                           err_msg="Usage: gt java add-testclass [project] [-p <package_prefix>] <testclasses>")
    project = extract_and_validate_project_from_args(args=args)
    
    # Detect options and their arguments
    package_flag_present = False
    unrecognized_opts = set()
    prefix_package = ""
    while args:
        opt = args.pop(0)
        if opt.startswith("-"):
            if opt == "-p":
                package_flag_present = True
                if args:
                    value = args.pop(0)
                    if not value.startswith("-"):
                        prefix_package = value
                    else:
                        args.insert(0, value)
            else:
                unrecognized_opts.add(opt)
        else:
            args.insert(0, opt)
            break
    
    ensure_sufficient_args(args=args, err_msg="Please specify at least one test class to create.")
    test_classes = [classname for classname in args]
    
    # Process options
    if unrecognized_opts:
        raise_unrecognized_opts_error(opts=unrecognized_opts, cmd="gt java add-testclass")
    if package_flag_present:
        if not prefix_package:
            raise Exception("The '-p' option must be followed by a package name.")
        test_classes = [".".join([prefix_package, classname]) for classname in test_classes]
    test_sources = [JavaSourceFile(classname=classname, project=project, src_type="test") for classname in test_classes]
    SourceFile.create_all(test_sources)


def _add_pkg(args: List[str]) -> None:
    ensure_sufficient_args(args=args, err_msg="Usage: gt java add-pkg [project] [-p <package_prefix>] [-t] <packages>")
    project = extract_and_validate_project_from_args(args=args)

    # Detect options
    include_test = False
    include_prefix = False
    prefix_package = ""
    unrecognized_opts = set()
    while args:
        opt = args.pop(0)
        if opt.startswith("-"):
            if opt == "-t":
                include_test = True
            elif opt == "-p":
                include_prefix = True
                if args:
                    value = args.pop(0)
                    if not value.startswith("-"):
                        prefix_package = value
                    else:
                        args.insert(0, value)
            else:
                unrecognized_opts.add(opt)
        else:
            args.insert(0, opt)
            break
    
    if unrecognized_opts:
        raise_unrecognized_opts_error(opts=unrecognized_opts, cmd="gt java add-pkg")
    
    ensure_sufficient_args(args=args, err_msg="Please specify at least one package to create.")
    pkgnames = [name for name in args]
    
    if include_prefix:
        if not prefix_package:
            raise Exception("The '-p' option must be followed by a prefix for the intended package(s)")
        pkgnames = [".".join([prefix_package, name]) for name in pkgnames]
    
    if include_test:
        test_packages = [JavaPackage(pkgname=pkgname, project=project, src_type="test") for pkgname in pkgnames]
    else:
        test_packages = []
    main_packages = [JavaPackage(pkgname=pkgname, project=project, src_type="main") for pkgname in pkgnames]
    Package.create_all(main_packages + test_packages)


def _add_project(args: List[str]) -> None:
    ensure_sufficient_args(args=args, err_msg="Usage: gt java add-project [--springboot [springboot options]] <project_names>\n\n"
                                              "For a full list of available springboot options, run 'curl https://start.spring.io'")
    if SINGLE_PROJECT_BUILD:
        response = input("The current build is a single-project build. "
                         "Do you still wish to add a new subproject? (y/n): ")
        response = response.lower()
        if (response == "y" or 
            response == "yes"):
            pass
        elif (response == "n" or 
              response == "no"):
            return
        else:
            print("Not a valid response")
            return

    # Process options
    unrecognized_opts = set()
    springboot_project = False
    springboot_parameters: Dict[str, str] = {}
    while args:
        opt = args.pop(0)
        if opt.startswith("-"):
            if opt == "--springboot":
                springboot_project = True
                # Parse springboot options
                while args:
                    springboot_opt = args.pop(0)
                    if springboot_opt.startswith("--"):
                        springboot_param_pattern = r"--(?P<parameter>[^\s]+)=(?P<value>[^\s]+)"
                        match = re.fullmatch(springboot_param_pattern, springboot_opt)
                        if match:
                            springboot_parameters[match.group("parameter")] = match.group("value")
                    else:
                        args.insert(0, springboot_opt)
                        break
            else:
                unrecognized_opts.add(opt)
        else:
            args.insert(0, opt)
            break
    if unrecognized_opts:
            raise_unrecognized_opts_error(opts=unrecognized_opts, cmd="gt java add-project")

    # The remaining items on the command line are assumed to be project names
    subprojects_specified = {name for name in args} # Remove possible duplicates
    if not subprojects_specified:
        print("Please specify the name of the subproject(s) to create.")
    else:
        # Create the subprojects
        if springboot_project:
            generate_springboot_subprojects(project_names=subprojects_specified, user_specified_parameters=springboot_parameters)
        else:
            generate_subprojects(project_names=subprojects_specified, project_type="java-application")
    


def _add_testpkg(args: List[str]) -> None:
    ensure_sufficient_args(args=args, err_msg="Usage: gt java add-testpkg [project] [-p <package_prefix>] <testpackages>")
    project = extract_and_validate_project_from_args(args=args)

    # Detect options
    include_prefix = False
    prefix_package = ""
    unrecognized_opts = set()
    while args:
        opt = args.pop(0)
        if opt.startswith("-"):
            if opt == "-p":
                include_prefix = True
                if args:
                    value = args.pop(0)
                    if not value.startswith("-"):
                        prefix_package = value
                    else:
                        args.insert(0, value)
            else:
                unrecognized_opts.add(opt)
        else:
            args.insert(0, opt)
            break

    if unrecognized_opts:
        raise_unrecognized_opts_error(opts=unrecognized_opts, cmd="gt java add-testpkg")
    ensure_sufficient_args(args=args, err_msg="Please specify at least one test package to create.")
    pkgnames = [name for name in args]

    if include_prefix:
        if not prefix_package:
            raise Exception("The '-p' option must be followed by a prefix for the intended package(s)")
        pkgnames = [".".join([prefix_package, name]) for name in pkgnames]

    test_packages = [JavaPackage(pkgname=pkgname, project=project, src_type="test") for pkgname in pkgnames]
    Package.create_all(test_packages)


def _ls_cmd(args: List[str]) -> None:
    if args:
        raise Exception("'gt java ls-cmd' does not take any arguments.")

    for cmd in COMMANDS:
        print(cmd)


def _ls_pkg(args: List[str]) -> None:
    # Detect options:
    list_test = False
    list_main = False
    unrecognized_opts = set()
    while args:
        opt = args.pop(0)
        if opt.startswith("-"):
            if opt == "-t":
                list_test = True
            elif opt == "-m":
                list_main = True
            else:
                unrecognized_opts.add(opt)
        else:
            args.insert(0, opt)
            break

    if unrecognized_opts:
        raise_unrecognized_opts_error(opts=unrecognized_opts, cmd="gt java ls-pkg")

    projects = []
    projects_dne = []
    projects_with_missing_src = []
    if SINGLE_PROJECT_BUILD:
        if args:
            print("All non-option arguments will be ignored for single-project builds.")
            print()
        projects = [p for p in PROJECTS]
    else:
        source = PROJECTS if not projects else args
        projects = [p for p in source]
    
    for p in projects:
        if p not in PROJECTS:
            projects_dne.append(p)
        else:
            src_root = os.path.join(PROJECTS[p], "src")
            if not os.path.isdir(src_root):
                projects_dne.append(src_root)
            else:
                os.chdir(src_root)
                basedirs = []

                if list_main:
                    basedirs.append("main/java")
                if list_test:
                    basedirs.append("test/java")
                if not basedirs:
                    basedirs = ["main/java", "test/java"]

                for basedir in basedirs:
                    if not os.path.isdir(basedir):
                        projects_with_missing_src.append(p)
                        break
                else:
                    print(f"{p}:")
                    for basedir in basedirs:
                        os.system(f"tree --noreport -d {basedir}")
                    print()

    if projects_dne:
        report_nonexisting_projects(projects_dne)

    if projects_with_missing_src:
        report_incomplete_or_missing_src_sets(projects=projects_with_missing_src, src_language="java")


def _rm_class(args: List[str]) -> None:
    ensure_sufficient_args(args=args, err_msg="Usage: gt java rm-class [project] [-t] [-p <package_prefix>] <classes>")
    project = extract_and_validate_project_from_args(args=args)

    # Detect options and their arguments
    include_test_tree = False
    package_flag_present = False
    unrecognized_opts = set()
    prefix_package = ""
    while args:
        opt = args.pop(0)
        if opt.startswith("-"):
            if opt == "-t":
                include_test_tree = True
            elif opt == "-p":
                package_flag_present = True
                if args:
                    value = args.pop(0)
                    if not value.startswith("-"):
                        prefix_package = value
                    else:
                        args.insert(0, value)
            else:
                unrecognized_opts.add(opt)
        else:
            args.insert(0, opt)
            break

    if unrecognized_opts:
        raise_unrecognized_opts_error(opts=unrecognized_opts, cmd="gt java rm-class")

    ensure_sufficient_args(args=args, err_msg="Please specify at least one class to remove.")
    
    # Process the options
    main_classes = [classname for classname in args]
    if package_flag_present:
        if not prefix_package:
            raise Exception("The '-p' option must be followed by a package name.")
        # Append the prefix package to all provided classes
        main_classes = [".".join([prefix_package, classname]) for classname in main_classes]

    if include_test_tree:
        test_classes = [classname + "Test" for classname in main_classes]
    else:
        test_classes = []
    
    test_sources = [JavaSourceFile(classname=classname, project=project, src_type="test") for classname in test_classes]
    main_sources = [JavaSourceFile(classname=classname, project=project, src_type="main") for classname in main_classes]
    SourceFile.remove_all(main_sources + test_sources)
    

def _rm_testclass(args: List[str]) -> None:
    ensure_sufficient_args(args=args, err_msg="Usage: gt java rm-testclass [project] [-p <package_prefix>] <testclasses>")
    project = extract_and_validate_project_from_args(args=args)

    # Detect options and their arguments
    package_flag_present = False
    unrecognized_opts = set()
    prefix_package = ""
    while args:
        opt = args.pop(0)
        if opt.startswith("-"):
            if opt == "-p":
                package_flag_present = True
                if args:
                    value = args.pop(0)
                    if not value.startswith("-"):
                        prefix_package = value
                    else:
                        args.insert(0, value)
            else:
                unrecognized_opts.add(opt)
        else:
            args.insert(0, opt)
            break

    if unrecognized_opts:
        raise_unrecognized_opts_error(opts=unrecognized_opts, cmd="gt java rm-testclass")

    ensure_sufficient_args(args=args, err_msg="Please specify at least one test class to remove.")

    # Process options
    test_classes = [classname for classname in args]
    if package_flag_present:
        if not prefix_package:
            raise Exception("The '-p' option must be followed by a package name.")
        test_classes = [".".join([prefix_package, classname]) for classname in test_classes]

    test_sources = [JavaSourceFile(classname=classname, project=project, src_type="test") for classname in test_classes]
    SourceFile.remove_all(test_sources)


def _rm_pkg(args: List[str]) -> None:
    ensure_sufficient_args(args=args, err_msg="Usage: gt java rm-pkg [project] [-p <package_prefix>] <packages>")
    project = extract_and_validate_project_from_args(args=args)

    # Detect options
    include_test = False
    include_prefix = False
    prefix_package = ""
    unrecognized_opts = set()
    while args:
        opt = args.pop(0)
        if opt.startswith("-"):
            if opt == "-t":
                include_test = True
            elif opt == "-p":
                include_prefix = True
                if args:
                    value = args.pop(0)
                    if not value.startswith("-"):
                        prefix_package = value
                    else:
                        args.insert(0, value)
            else:
                unrecognized_opts.add(opt)
        else:
            args.insert(0, opt)
            break

    if unrecognized_opts:
        raise_unrecognized_opts_error(opts=unrecognized_opts, cmd="gt java rm-pkg")

    ensure_sufficient_args(args=args, err_msg="Please specify at least one package to remove.")
    pkgnames = [name for name in args]

    if include_prefix:
        if not prefix_package:
            raise Exception("The '-p' option must be followed by a prefix for the intended package(s)")
        pkgnames = [".".join([prefix_package, name]) for name in pkgnames]

    if include_test:
        test_packages = [JavaPackage(pkgname=pkgname, project=project, src_type="test") for pkgname in pkgnames]
    else:
        test_packages = []
    main_packages = [JavaPackage(pkgname=pkgname, project=project, src_type="main") for pkgname in pkgnames]
    Package.remove_all(main_packages + test_packages)


def _rm_testpkg(args: List[str]) -> None:
    ensure_sufficient_args(args=args, err_msg="Usage: gt java rm-testpkg [project] <testpackages>")
    project = extract_and_validate_project_from_args(args=args)

    # Detect options
    include_prefix = False
    prefix_package = ""
    unrecognized_opts = set()
    while args:
        opt = args.pop(0)
        if opt.startswith("-"):
            if opt == "-p":
                include_prefix = True
                if args:
                    value = args.pop(0)
                    if not value.startswith("-"):
                        prefix_package = value
                    else:
                        args.insert(0, value)
            else:
                unrecognized_opts.add(opt)
        else:
            args.insert(0, opt)
            break

    if unrecognized_opts:
        raise_unrecognized_opts_error(opts=unrecognized_opts, cmd="gt java rm-testpkg")
    
    ensure_sufficient_args(args=args, err_msg="Please specify at least one test package to remove.")
    pkgnames = [name for name in args]

    if include_prefix:
        if not prefix_package:
            raise Exception("The '-p' option must be followed by a prefix for the intended package(s)")
        pkgnames = [".".join([prefix_package, name]) for name in pkgnames]

    test_packages = [JavaPackage(pkgname=pkgname, project=project, src_type="test") for pkgname in pkgnames]
    Package.remove_all(test_packages)


def _tree(args: List[str]) -> None:
    # Syntax: gt java tree [subprojects] [options]
    projects = []
    if SINGLE_PROJECT_BUILD:
        if args:
            print("All non-option arguments will be ignored for single-project builds.")
            print()
        projects.append(os.path.basename(ROOT_PROJECT))
    else:
        # Consume entries until the first option is encountered
        while args:
            entry = args.pop(0)
            if not entry.startswith("-"):
                if not SINGLE_PROJECT_BUILD:
                    projects.append(entry)
                # For single-project builds, all non-option arguments will be ignored
            else:
                args.insert(0, entry)
                break
        if not projects:
            # List all projects if none are specified
            projects = [p for p in PROJECTS]

    # Detect options
    m_flag_present = False
    t_flag_present = False
    unrecognized_opt = set()
    while args:
        opt = args.pop(0)
        if opt == "-m":
            m_flag_present = True
        elif opt == "-t":
            t_flag_present = True
        else:
            unrecognized_opt.add(opt)

    if unrecognized_opt:
        raise_unrecognized_opts_error(opts=unrecognized_opt, cmd="gt java tree")

    projects_dne = []
    projects_without_java_src_set = []

    for p in projects:
        if p not in PROJECTS:
            projects_dne.append(p)
        else:
            src_root = os.path.join(PROJECTS[p], "src")
            if not os.path.isdir(src_root):
                projects_without_java_src_set.append(p)
            else:
                os.chdir(src_root)
                basedirs = []
                if m_flag_present:
                    basedirs.append("main/java")
                if t_flag_present:
                    basedirs.append("test/java")
                if not basedirs:
                    basedirs = ["main/java", "test/java"]
                for basedir in basedirs:
                    if not os.path.isdir(basedir):
                        projects_without_java_src_set.append(p)
                        break
                else:
                    print(f"{p}:")
                    for basedir in basedirs:
                        os.system(f"tree --noreport {basedir}")
                print()

    if projects_dne:
        report_nonexisting_projects(projects_dne)

    if projects_without_java_src_set:
        report_incomplete_or_missing_src_sets(projects_without_java_src_set, src_language="java")


COMMANDS = {
    "add-class"     : _add_class,
    "add-testclass" : _add_testclass,
    "add-pkg"       : _add_pkg,
    "add-testpkg"   : _add_testpkg,
    "add-project"   : _add_project,
    "ls-cmd"        : _ls_cmd,
    "ls-pkg"        : _ls_pkg,
    "rm-class"      : _rm_class,
    "rm-pkg"        : _rm_pkg,
    "rm-testclass"  : _rm_testclass,
    "rm-testpkg"    : _rm_testpkg,
    "tree"          : _tree
}

import os.path, subprocess
from .. import *
from ..utils import *


def _add_project(args: List[str]) -> None:
    pass


def _ls_cmd(args: List[str]) -> None:
    if args:
        raise Exception("The 'gt - ls-cmd' command does not accept any argument.")
    for cmd in COMMANDS:
        print(cmd)


def _projects(args: List[str]) -> None:
    # Collect options
    plain_format = False
    unrecognized_opts = set()
    while args:
        opt = args.pop(0)
        if opt.startswith("-"):
            if opt == "--plain-format":
                plain_format = True
            else:
                unrecognized_opts.add(opt)
        else:
            args.insert(0, opt)
            break

    if args:
        raise Exception("The 'gt - projects' command takes no argument.")

    if unrecognized_opts:
        raise_unrecognized_opts_error(opts=unrecognized_opts, cmd="gt - projects")

    if not plain_format:
        if SINGLE_PROJECT_BUILD:
            raise Exception("A single-project build does not contain any subprojects.")
        
        included_projects = get_included_subprojects()
        
        print("Projects list:")
        
        for project in PROJECTS:
            if project in included_projects:
                symbol = "+"
            elif project == os.path.basename(ROOT_PROJECT):
                symbol = "∗"
            else:
                symbol = "-"
            print(f"{symbol} {project}")
    else:
        for project in PROJECTS:
            print(project)


def _reports(args: List[str]) -> None:
    if SINGLE_PROJECT_BUILD:
        projects = [os.path.basename(ROOT_PROJECT)]
    else:
        if not args:
            # No subprojects specified
            # Open the reports of all included subprojects
            projects = get_included_subprojects()
        else:
            projects = [project for project in args]

    nonexistent_subprojects = []
    subprojects_without_reports = []
    reports_to_open     = []
    for s in projects:
        if s not in PROJECTS:
            nonexistent_subprojects.append(s)
        else:
            index_html = os.path.join(PROJECTS[s], "build/reports/tests/test/index.html")
            if not os.path.isfile(index_html):
                subprojects_without_reports.append(s)
            else:
                reports_to_open.append(index_html)

    for report in reports_to_open:
        subprocess.Popen(args=["xdg-open", report])

    for s in subprojects_without_reports:
        print(f"✘ No test reports are available for '{s}'")

    for s in nonexistent_subprojects:
        print(f"✘ Invalid subproject '{s}'")


def _root(args:List[str]) -> None:
    if args:
        raise Exception("The 'gt - root' command does not accept any arguments.")

    # Return the full path of the root project
    print(ROOT_PROJECT)


def _tree(args: List[str]) -> None:
    # Syntax: gt - tree [subprojects] [options]
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

    # Process options
    m_flag_present = False
    t_flag_present = False
    unrecognized_opts = set()
    while args:
        opt = args.pop(0)
        if opt.startswith("-"):
            if opt == "-m":
                m_flag_present = True
            elif opt == "-t":
                t_flag_present = True
            else:
                unrecognized_opts.add(opt)
        else:
            args.insert(0, opt)
            break

    if unrecognized_opts:
        raise_unrecognized_opts_error(opts=unrecognized_opts, cmd="gt - tree")

    projects_dne = []
    projects_without_src_set = []
    for p in projects:
        if p not in PROJECTS:
            projects_dne.append(p)
        else:
            src_root = os.path.join(PROJECTS[p], "src")
            if not os.path.isdir(src_root):
                projects_without_src_set.append(p)
            else:
                os.chdir(src_root)
                basedirs = []
                if m_flag_present:
                    basedirs.append("main")
                if t_flag_present:
                    basedirs.append("test")
                if not basedirs:
                    basedirs = ["main", "test"]
                for basedir in basedirs:
                    if not os.path.isdir(basedir):
                        projects_without_src_set.append(p)
                        break
                else:
                    print(f"{p}:")
                    for basedir in basedirs:
                        os.system(f"tree --noreport {basedir}")
                print()

    if projects_without_src_set:
        report_incomplete_or_missing_src_sets(projects_without_src_set)
    if projects_dne:
        report_nonexisting_projects(projects_dne)

COMMANDS = {
    "add-project" : _add_project,
    "ls-cmd"      : _ls_cmd,
    "projects"    : _projects,
    "reports"     : _reports,
    "root"        : _root,
    "tree"        : _tree
}

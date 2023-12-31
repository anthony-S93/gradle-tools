# Initialize application state
import os, os.path

# Obtain installation directory
APP_HOME = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

# Locate the root project first
CWD  = os.getcwd()
HOME = os.path.expanduser("~")

if (os.path.commonpath([CWD, HOME]) == HOME):
    search_endpoint = HOME
else:
    search_endpoint = "/"

search_dir = CWD
ROOT_PROJECT = ""
SETTINGS_FILE = ""
SINGLE_PROJECT_BUILD = False

while search_dir != search_endpoint:
    settings_files = (
        os.path.join(search_dir, "settings.gradle"),
        os.path.join(search_dir, "settings.gradle.kts")
    )
    for sf in settings_files:
        if os.path.isfile(sf):
            ROOT_PROJECT = search_dir
            SETTINGS_FILE = sf
            break
    if ROOT_PROJECT:
        break
    else:
        search_dir = os.path.dirname(search_dir)

if not ROOT_PROJECT:
    # Could be a single-project build with no settings file
    # For such builds, the build script becomes the root marker
    search_dir = CWD
    while search_dir != search_endpoint:
        build_scripts = (
            os.path.join(search_dir, "build.gradle"),
            os.path.join(search_dir, "build.gradle.kts")
        ) 
        for script in build_scripts:
            if os.path.isfile(script):
                ROOT_PROJECT = search_dir
                break
        if ROOT_PROJECT:
            break
        else:
            search_dir = os.path.dirname(search_dir)

    if not ROOT_PROJECT:
        print("Not a gradle project.")
        os._exit(1)

# Detect all subprojects first
PROJECTS = {}
dir_iterator = os.walk(ROOT_PROJECT)
_, subdirs, files = next(dir_iterator)

for dir in subdirs:
    if (dir.startswith(".") or
        dir in ("buildSrc", "gradle")):
        continue
    # dir is a subproject if and only if it has a build script
    dir_abs = os.path.join(ROOT_PROJECT, dir)
    if ((os.path.isfile(os.path.join(dir_abs, "build.gradle.kts"))) or
        (os.path.isfile(os.path.join(dir_abs, "build.gradle.")))):
        PROJECTS[dir] = dir_abs

if not PROJECTS:
    # No subprojects detected
    # Must be a single-project build
    SINGLE_PROJECT_BUILD = True
    PROJECTS[os.path.basename(ROOT_PROJECT)] = ROOT_PROJECT
else:
    # Include the root project in multi-project builds
    # if and only if the root project has a src set
    root_src_set = os.path.join(ROOT_PROJECT, "src")
    if os.path.isdir(root_src_set):
        PROJECTS[os.path.basename(ROOT_PROJECT)] = ROOT_PROJECT

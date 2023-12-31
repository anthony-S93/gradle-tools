_extract_language() {
    local words language
    words=("$@")
    language="${words[1]}"

    case "$language" in 
        java|kotlin|cpp|-)
            echo "$language"
            ;;
    esac
}


_extract_pkg_prefix() {
    local words pkg_prefix
    words=("$@")
    pkg_prefix=""
    for index in "${!words[@]}"
    do
        if [ "${words[$index]}" = "-p" ]
        then
            pkg_prefix="${words[$((index + 1))]}"
            break
        fi
    done
    echo "$pkg_prefix"
}


_extract_subproject() {
    local words root_project subproject
    words=("$@")
    root_project=$(gt - root)
    subproject=""
    if [ -d "$root_project/${words[3]}" ]
    then
        subproject="${words[3]}"
    fi
    echo "$subproject"
}


_get_src_file_extension() {
    local language
    language="$1"

    case "$language" in 
        java)
            echo ".java"
            ;;
        kotlin)
            echo ".kt"
            ;;
        cpp)
            echo ".cpp"
            ;;
    esac
}


_get_src_dir() {
    local args src_type words
    args=("$@")
    src_type="${args[0]}"
    words=("${args[@]:1}")

    local language src_dir root_project project
    language=$(_extract_language "${words[@]}")
    project=$(_extract_subproject "${words[@]}")
    root_project=$(gt - root)

    if [ "$language" ]
    then
        if [ "$project" ]
        then
            src_dir="${root_project}/${project}/src/${src_type}/${language}"
        else
            src_dir="${root_project}/src/${src_type}/${language}"
        fi
    fi

    if [ -d "$src_dir" ]
    then
        echo "$src_dir"
    fi
}


_list_classes() {
    local args class_type words src_dir pkg_prefix
    args=("$@")
    class_type="${args[0]}"
    words=("${args[@]:1}")
    src_dir=$(_get_src_dir "$class_type" "${words[@]}")
    
    if [ "$src_dir" ]
    then
        pkg_prefix=$(_extract_pkg_prefix "${words[@]}")
        if [ "$pkg_prefix" ] 
        then
            local pkg_dir
            pkg_dir=$(echo "$pkg_prefix" | tr "." "/")
            src_dir="$src_dir/$pkg_dir"
        fi
        language="${words[1]}"
        file_extension=$(_get_src_file_extension "$language")
        for classname in $(find "$src_dir" -name "*$file_extension" -printf "%P\n" | tr "/" ".")
        do
            basename "$classname" ".$language"
        done
    fi
}


_list_pkgs() {
    local args words pkg_type src_dir
    args=("$@")
    pkg_type="${args[0]}" # test or main?
    words=("${args[@]:1}")
    src_dir=$(_get_src_dir "$pkg_type" "${words[@]}")
    if [ "$src_dir" ]
    then
        if [ "$prev" != "-p" ]
        then
            local pkg_prefix
            pkg_prefix=$(_extract_pkg_prefix "${words[@]}")
            if [ "$pkg_prefix" ]
            then
                local pkg_dir
                pkg_dir=$(echo "$pkg_prefix" | tr "." "/")
                src_dir="$src_dir/$pkg_dir"
            fi
        fi
        find "$src_dir" -mindepth 1 -type d -printf "%P\n" | tr "/" "."
    fi
}


_gt_completion() {
    if gt >/dev/null 2>&1
    then
        local cur prev words
        _init_completion || return

        case "$prev" in
            gt)
                # Suggest all supported languages
                readarray -t COMPREPLY < <(compgen -W "- java" -- "$cur")
                ;;
            java|-)
                # Suggest available subcommands for the specified language
                readarray -t COMPREPLY < <(compgen -W "$(gt "$prev" ls-cmd)" -- "$cur")
                ;;
            add-class|add-testclass|rm-class|rm-testclass|add-pkg|add-testpkg|rm-pkg|rm-testpkg|ls-pkg|reports)
                # Suggest all avaiable projects
                readarray -t COMPREPLY < <(compgen -W "$(gt - projects --plain-format)" -- "$cur")
                ;;
            add-project)
                readarray -t COMPREPLY < <(compgen -W "--springboot" -- "$cur")
                ;;
            -p)
                # Suggest available packages for subcommands that support the -p flag
                local cmd="${words[2]}"
                case "$cmd" in
                    add-class|rm-class|add-pkg|rm-pkg)
                        readarray -t COMPREPLY < <(compgen -W "$(_list_pkgs "main" "${words[@]}")" -- "$cur")
                        ;;
                    add-testclass|rm-testclass|add-testpkg|rm-testpkg)
                        readarray -t COMPREPLY < <(compgen -W "$(_list_pkgs "test" "${words[@]}")" -- "$cur")
                        ;;
                esac
                ;;
            *)
                # Suggestion items depend on the subcommand being invoked
                local cmd="${words[2]}"
                case "$cmd" in
                    add-project)
                        local language flag
                        language=${words[1]}
                        flag=${words[3]}
                        case "$language" in 
                            java|-)
                                if [ "$flag" = "--springboot" ]
                                then
                                    local springboot_params="--applicationName \
                                                             --artifactId \
                                                             --bootVersion \
                                                             --dependencies \
                                                             --description \
                                                             --groupId \
                                                             --javaVersion \
                                                             --name \
                                                             --packageName \
                                                             --packaging \
                                                             --type \
                                                             --version"
                                    readarray -t COMPREPLY < <(compgen -W "$springboot_params" -- "$cur")
                                fi
                                ;;
                        esac
                        ;;
                    rm-class)
                        readarray -t COMPREPLY < <(compgen -W "$(_list_classes "main" "${words[@]}")" -- "$cur")
                        ;;
                    rm-testclass)
                        readarray -t COMPREPLY < <(compgen -W "$(_list_classes "test" "${words[@]}")" -- "$cur")
                        ;;
                    rm-pkg)
                        readarray -t COMPREPLY < <(compgen -W "$(_list_pkgs "main" "${words[@]}")" -- "$cur")
                        ;;
                    rm-testpkg)
                        readarray -t COMPREPLY < <(compgen -W "$(_list_pkgs "test" "${words[@]}")" -- "$cur")
                        ;;
                    tree)
                        readarray -t COMPREPLY < <(compgen -W "$(gt - projects --plain-format)" -- "$cur")
                        ;;
                esac
                ;;
        esac
    fi
    # No completion outside a gradle project
}

complete -F _gt_completion gt

#!/bin/sh
app_home="$(dirname "$(readlink -f "$0")")"
completion_dir="$HOME/.local/share/bash-completion/completions"

if [ "$(id -u)" = 0 ]
then
    echo "The setup script should not be run with sudo"
    echo "Aborting..."
    exit 1
else
    # Drop a symlink to /usr/local/bin
    if type gt > /dev/null 2>&1
    then
        echo "A binary named 'gt' already exists in PATH"
        echo "Aborting..."
        exit 1
    fi

    if [ -e "/usr/local/bin/gt" ]
    then
        echo "Unable to create a symlink named 'gt' inside /usr/local/bin"
        echo "Please add the bin/ directory of this repo to your PATH manually"
    else
        echo "==> Creating symlink inside /usr/local/bin"
        if sudo ln -s "$app_home/bin/gt" "/usr/local/bin/gt" 2>&1
        then
            echo "==> Symlink /usr/local/bin/gt created"
        else
            echo "==> Failed to create symlink /usr/local/bin/gt"
            echo "Please add the bin/ directory of this repo to your PATH manually"
        fi
    fi

    # Add bash completion script
    if [ -d "$completion_dir" ]
    then
        echo "==> Adding bash completion"
        ln -s "$app_home/bash-completion/gt.bash" "$completion_dir/gt.bash"
    else
        if [ ! -e "$completion_dir" ]
        then
            echo "==> Adding bash completion"
            mkdir -p "$completion_dir"
            ln -s "$app_home/bash-completion/gt.bash" "$completion_dir/gt.bash"
        else
            echo "==> Failed to add bash-completion"
            echo "A file already exists at $completion_dir"
        fi
    fi
fi


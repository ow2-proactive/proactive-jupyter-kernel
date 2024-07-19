#!/bin/bash

set -e

VERSION=$1
PROACTIVE_PYTHON_SDK_RELEASE=$2
PYTHON=python3
PROACTIVE_PYTHON_SDK_HOME="../proactive-python-client"
ENV="env$VERSION"

create_venv() {
    echo "Creating virtual environment $ENV..."
    $PYTHON -m venv $ENV
}

update_venv() {
    echo "Updating virtual environment $ENV..."
    $ENV/bin/$PYTHON -m pip install --upgrade pip setuptools wheel twine
    $ENV/bin/$PYTHON -m pip install -r requirements$VERSION.txt
    $ENV/bin/$PYTHON -m pip install --global-option=build_ext \
        --global-option="-I$(brew --prefix graphviz)/include/" \
        --global-option="-L$(brew --prefix graphviz)/lib/" \
        pygraphviz==1.9
    $ENV/bin/$PYTHON -m pip -V
}

uninstall_proactive() {
    echo "Uninstalling proactive package..."
    . $ENV/bin/activate && $PYTHON -m pip uninstall -y proactive
    echo "Proactive package uninstalled."
}

install_proactive() {
    case "$PROACTIVE_PYTHON_SDK_RELEASE" in
        "test")
            echo "Installing the latest test version of proactive from TestPyPI..."
            . $ENV/bin/activate && $PYTHON -m pip install --upgrade --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple --pre proactive
            ;;
        "local")
            echo "Installing the latest local version of proactive..."
            . $ENV/bin/activate
            for zip in $PROACTIVE_PYTHON_SDK_HOME/dist/*.zip; do
                $PYTHON -m pip install "$zip"
            done
            ;;
        *)
            echo "Installing the latest pre-release of proactive..."
            . $ENV/bin/activate && $PYTHON -m pip install --upgrade --pre proactive
            ;;
    esac
}

create_or_update_venv() {
    if [ -d "$ENV" ]; then
        echo "Virtual environment $ENV already exists."
        read -p "Do you want to delete it and create a new one? [y/N] " answer
        case $answer in
            [Yy]* )
                echo "Deleting and recreating the virtual environment..."
                rm -rf $ENV
                create_venv
                ;;
            * )
                echo "Using the existing virtual environment."
                ;;
        esac
    else
        create_venv
    fi

    update_venv
    uninstall_proactive
    install_proactive

    echo "Virtual environment is ready."
}

create_or_update_venv
# bowl

A TUI client for [euphoria.io](https://euphoria.io)

## Installation

Ensure that you have at least Python 3.7 installed.

To install **bowl** or update your installation to the latest version, run the
following command wherever you want to install or have installed **bowl**:
```
$ pip install git+https://github.com/Garmelon/bowl@v1.0.0
```

The use of [venv](https://docs.python.org/3/library/venv.html) is recommended.

## Example setup

In this example, `python` refers to at least Python 3.7, as mentioned above.

This example uses `venv`, so that `pip install` does not install any packages
globally.

First, create a folder and a venv environment inside that folder.
```
$ mkdir bowl
$ cd bowl
$ python -m venv .
$ . bin/activate
```

Then, install **bowl**.
```
$ pip install git+https://github.com/Garmelon/bowl@v1.0.0
```

Create a config file containing all default values in the default config file
location.
```
$ mkdir -p ~/.config/bowl/
$ bowl --export-defaults ~/.config/bowl/bowl.yaml
$ vim ~/.config/bowl/bowl.yaml
```

Run **bowl** (have fun!).
```
$ bowl
```

Exit the venv environment again.
```
$ deactivate
```

Subsequent runs of the program might look like this:
```
$ cd bowl
$ . bin/activate
$ bowl
$ deactivate
```

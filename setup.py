from setuptools import setup

setup(
        name="bowl",
        version="0.0.1",
        packages=[
            "bowl",
            "bowl.euphoria",
        ],
        entry_points={
            "console_scripts": [
                "bowl = bowl.euphoria:launch_single_room_application",
            ],
        },
        install_requires=[
            "PyYAML >= 5.1.1",
            "urwid >= 2.0.1",
            "websockets >= 7.0",
            "yaboli @ git+https://github.com/Garmelon/yaboli@v1.1.4",
        ],
)

# When updating the version, also:
# - update the README.md installation instructions
# - update the changelog
# - set a tag on the update commit

=============================
Samsung Helper - Telegram Bot
=============================

.. image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v2.json
    :target: https://github.com/charliermarsh/ruff
    :alt: Ruff

.. image:: https://badges.crowdin.net/sambot/localized.svg
    :target: https://crowdin.com/project/sambot/
    :alt: crowdin status

.. image:: https://results.pre-commit.ci/badge/github/HitaloM/Samsung-Helper/main.svg
   :target: https://results.pre-commit.ci/latest/github/HitaloM/Samsung-Helper/main
   :alt: pre-commit.ci status

Samsung Helper is a Telegram bot that was originally created to send notifications about new Samsung firmwares to the `@SamFirm <https://t.me/SamFirm>`_, channel.
However, it also has other functionalities for users of Samsung Galaxy devices.

How to contribute
=================
Every open source project lives from the generous help by contributors that sacrifices their time and Samsung Helper is no different.

Translations
------------
Translations should be done in our `Crowdin Project <https://crowdin.com/project/sambot>`_,
as Crowdin checks for grammatical issues, provides improved context about the string to be translated and so on,
thus possibly providing better quality translations. But you can also submit a pull request if you prefer to translate that way.

Bot setup
---------
Below you can learn how to set up the Samsung Helper project.

Requirements
~~~~~~~~~~~~
- Python 3.11.X.
- An Unix-like operating system (Windows isn't supported).

Instructions
~~~~~~~~~~~~
1. Create a virtualenv (This step is optional, but **highly** recommended to avoid dependency conflicts)

   - ``python3 -m venv .venv`` (You don't need to run it again)
   - ``. .venv/bin/activate`` (You must run this every time you open the project in a new shell)

2. Install dependencies from the pyproject.toml with ``python3 -m pip install . -U``.
3. Go to https://my.telegram.org/apps and create a new app.
4. Create a new ``config.env`` in ``data/``, there is a ``config.example.env`` file for you to use as a template.
5. After completing the ``config.env`` file, run ``python3 -m sambot`` to start the bot.

Tools
~~~~~
- Use `black <https://github.com/psf/black/>`_ to format your code.
- Use `ruff <https://pypi.org/project/ruff/>`_ to lint your code.
- We recommend using `pre-commit <https://pre-commit.com/>`_ to automate the above tools.
- We use VSCode and recommend it with the Python, Pylance and Intellicode extensions.

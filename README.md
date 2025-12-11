<!-- Copyright (c) 2025, AgriTheory and contributors
For license information, please see license.txt-->

## Public Calendar

An application with electronic payments utilities for ERPNext.

### Installation Guide

First, set up a new bench and substitute a path to the python version to use. Python should be 3.10 latest for `version-15`. These instructions use [pyenv](https://github.com/pyenv/pyenv) for managing environments.
```shell
bench init --frappe-branch version-15 {{ bench name }} --python ~/.pyenv/versions/3.10.13/bin/python3
```

Create a new site in that bench
```shell
cd {{ bench name }}
bench new-site {{ site name }} --force --db-name {{ site name }}
bench use {{ site name }}
```

Download apps
```shell
bench get-app erpnext --branch version-15
bench get-app public_calendar --branch version-15 https://github.com/agritheory/public_calendar.git 
```

Install the apps to your site
```shell
bench --site {{ site name }} install-app public_calendar
```

Set developer mode in `site_config.json`
```shell
nano sites/{{ site name }}/site_config.json
# Add this line:
  "developer_mode": 1,

```
Install pre-commit:
```shell
# ~/frappe-bench/apps/public_calendar/
pre-commit install
```

Add the site to your computer's hosts file to be able to access it via: `http://{{ site name }}:[8000]`. You'll need to enter your root password to allow your command line application to make edits to this file.
```shell
bench --site {{site name}} add-to-hosts
```

Launch your bench (note you should be using Node.js v20)
```shell
bench start
```

To run `mypy` locally:
```shell
source env/bin/activate
mypy ./apps/public_calendar --ignore-missing-imports
```

To run tests locally on the test data:
```shell
source env/bin/activate
pytest ./apps/public_calendar/public_calendar/tests/ -s --disable-warnings
```

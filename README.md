Requirements:
=
- PostgrеSQL
- Python: 3.11
For the first time
=
- create database
- create virtual environment: python3 -m venv odoo-venv
- Activate virtual environment: source odoo-venv/bin/activate
- Install dependencies: pip install -r requirements.txt
- Create the config file: cp odoo/debian/odoo.conf /path/to/your/odoo.conf
> [options]
addons_path = D:\python\odoo18-py3.10\addons, D:\python\odoo18-py3.10\odoo\addons
db_host = localhost
db_user = postgres
db_maxconn = 64
db_maxconn_gevent = False
db_name = False
db_password = 123456
db_port = 5432
db_replica_host = False
db_replica_port = False
db_sslmode = prefer
db_template = template0
default_productivity_apps = True
http_port = 8081

Start Project
=
- For the first start: python3 odoo-bin -c odoo.conf -i base
- Next start: python3 odoo-bin -c odoo.conf

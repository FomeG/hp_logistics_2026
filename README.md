# Requirements

- PostgrеSQL >15
- Python: >3.10

# Installation

### 1. Clone the repository


1. clone the repository


    ```bash
    git clone https://gitlab.com/hplogistics/odoo.git
    cd odoo
    ```

    >**NOTE**: This is `main` branch, when you do "cd odoo", you are in the root folder of your project

    >**EXTRA**: After `cd odoo` you can run: ```code .``` (if you use VS Code) or ```pycharm .``` (if you use pycharm), it is to open the correspond IDE along with the repo.



<a id="step-copy-addons"></a> 

2. copy the `addons` folder in the main branch and paste it into somewhere else in the same disk as the repo

    >**IMPORTANT**: Its path will be added to the `odoo.conf` file later on






3. in the root folder:

    ```bash
    git checkout dev
    ```

    You should be able to see the project's custom modules here, most branches should be based from dev

### 2. Create virtual environment
```bash
python3 -m venv .venv

# or if your system does not recognize python3:
python -m venv .venv
```


### 3. Activate virtual environment
if you are using Linux/MacOS/WSL:
```bash
source .venv/bin/activate
```

if you use Windows CMD or Powershell:
```batch
.venv\Scripts\activate
```

if you use Git Bash on windows:
```bash
source .venv/Scripts/activate
```



### 4. Install dependencies
```bash
# if you use Linux/MacOs/WSL/Git Bash:
./pip_install.sh

# if you use Windows CMD:
pip_install.bat

# if you use Powershell:
.\pip_install.bat
```

>**NOTE**: `pip_install.bat/sh` are automation scripts used to install all required Python dependencies for the project


### 5. Create the odoo config file

```bash
python3 odoo-bin --save --config odoo.conf --stop-after-init

# or if your system does not recognize python3:
python odoo-bin --save --config odoo.conf --stop-after-init
```
>**NOTE**: This will create a new file named `odoo.conf` in your project root folder



### 6. Edit Configuration (Important)

Open the newly created `odoo.conf` file and modify the following required fields:


#### 1. Update `addons_path`
- Delete the generated addons_path line and Replace it with this line to include project modules:

    ```ini
    addons_path = ./odoo/addons, ./modules, ./modules/connector, ./modules/queue_job
    ```

    >**IMPORTANT**: you **MUST** add [this addons folder](#step-copy-addons) absolute path into `addons_path`

    >**NOTE**: All paths can be absolute paths. Ensure they are correct, incorrect paths will cause "Module not found" errors.


#### 2. Basic Settings
- Update database credentials and ports to match your local environment:

    ```ini
    db_host = localhost     
    db_port = 5432
    db_user = openpg        ; Your PostgreSQL username
    db_password = your_pwd  ; Your PostgreSQL password
    db_name = your_db_name  ; Any name you want for your database
    http_port = 8069        ; You can change this port if this port is busy
    ```

    >**NOTE**: You can also add your project API Keys in `odoo.conf`

# Start Project
- For the first start: 
    ```bash
    python3 odoo-bin -c odoo.conf -i base

    # or if your system does not recognize python3:
    python odoo-bin -c odoo.conf -i base
    ```

- Next start: 
    ```bash
    python3 odoo-bin -c odoo.conf

    # or if your system does not recognize python3:
    python odoo-bin -c odoo.conf
    ```
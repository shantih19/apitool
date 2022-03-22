#!/bin/python
import os
import sys
from jinja2 import Template
import nginx
from yaml import load, CLoader as Loader
import dbus

API_DIR = '/home/ubuntu/api'

def main():
    if len(sys.argv) < 2:
        print("Wrong usage.")
        showHelp()
        sys.exit(-1)
    if sys.argv[1] == 'create':
        createProject()
    elif sys.argv[1] == 'deploy':
        deployProject()
    elif sys.argv[1] == 'help':
        showHelp()
    else:
        print("Wrong usage.")
        showHelp()
        sys.exit(-1)
    sys.exit(0)

def createProject():
    try:
        if len(sys.argv) > 4:
            raise Exception
        project_name = sys.argv[2]
        project_desc = sys.argv[3]
    except:
        print("Wrong usage.")
        showHelp()
        sys.exit(-1)
    project_path = os.path.join(API_DIR, project_name)
    try:
        os.mkdir(project_path, 0o775)
    except FileExistsError:
        print('Folder already exists.')
        sys.exit(-1)
    for l in os.listdir('skeleton'):
        with open('skeleton/' +  l, 'r') as f:
            rendered = Template(f.read()).render(api_name=project_name, api_description=project_desc)
            filename = Template(l).render(api_name=project_name)
            with open(os.path.join(project_path, filename), 'w+') as f_:
                f_.write(rendered)
    print("Done! Have a nice day :3")

def deployProject():
    if os.geteuid() != 0:
        print("You need root privileges to deploy.")
        sys.exit(-1)
    try:
        if len(sys.argv) > 3:
            raise Exception
        project_name = sys.argv[2]
    except:
        print("Wrong usage.")
        showHelp()
        sys.exit(-1)
    try:
        with open(os.path.join(API_DIR, project_name, "config.yaml"), 'r') as meta:
            project_desc=load(meta, Loader=Loader)['description']   
    except FileNotFoundError:
        print("Project not found or does not exist.")
        sys.exit(-1)
    _add_nginx_config(project_name)
    _create_systemd_daemon(project_name, project_desc)
    _reload_daemons(project_name)
    print("Done! Have a nice day :3")
    
def _add_nginx_config(name):
    conf = nginx.loadf('/etc/nginx/sites-available/api')
    conf.server.add(
         nginx.Location('/'+name,
            nginx.Key('include', 'proxy_params'),
            nginx.Key('proxy_pass', 'http://unix:' + os.path.join(API_DIR, name, name+'.sock'))
        )
    )
    nginx.dumpf(conf, '/etc/nginx/sites-available/api')

def _create_systemd_daemon(name, desc):
    with open('skeleton.service', 'r') as f:
            rendered = Template(f.read()).render(api_name=name, api_description=desc)
            service_file = os.path.join('/etc/systemd/system', name + 'api.service' )
            try:
                with open(service_file, 'x') as f_:
                    f_.write(rendered)
            except FileExistsError:
                print('Service file already exists.')
                sys.exit(-1)

def _reload_daemons(name):
    system_bus = dbus.SystemBus()
    systemd1 = system_bus.get_object('org.freedesktop.systemd1', '/org/freedesktop/systemd1')
    manager = dbus.Interface(systemd1, 'org.freedesktop.systemd1.Manager')
    manager.EnableUnitFiles([name+'api.service'], False, True)
    manager.Reload()
    job = manager.RestartUnit(name+'api.service', 'fail')
    job = manager.RestartUnit('nginx.service', 'fail')

def showHelp():
    print("Usage: apitools.py command {arguments}\n")
    print("Commands:")
    print(" create - creates project structure")
    print("  arguments: name \"description\"")
    print(" deploy - creates project unit service and nginx config - requires root priviledges")
    print("  arguments: name")
    print(" help - show this message")
    print("\nhave a nice day :3")

if __name__ == "__main__":
    main()

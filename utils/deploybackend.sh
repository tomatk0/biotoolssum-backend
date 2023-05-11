#!/bin/bash

echo "ENTER THE IP ADDRESS OF THIS VM"
read ip
echo "export IP_ADDRESS=\"http://$ip\"" | sudo tee -a /etc/environment

echo "ENTER A VALID GITHUB TOKEN"
read token
echo "export GITHUB_TOKEN=\"$token\"" | sudo tee -a /etc/environment

source /etc/environment

CURRENT_USER=$(whoami)

echo "GITHUB_TOKEN=$token" | sudo tee -a /home/$CURRENT_USER/biotoolssum-backend/.env

# INSTALLING NECESSARY PYTHON LIBRARIES

sudo apt update

sudo apt install python3-pip python3-dev build-essential libssl-dev libffi-dev python3-setuptools python3-venv

python3 -m venv /home/$CURRENT_USER/biotoolssum-backend/venv

source /home/$CURRENT_USER/biotoolssum-backend/venv/bin/activate
pip install wheel flask gunicorn requests sqlalchemy flask_cors celery pymysql cryptography python-dotenv
deactivate

# SETTING UP LOG FILES

sudo mkdir /var/log/biotoolssum

sudo touch /var/log/biotoolssum/gunicorn_error.log
sudo chmod 755 /var/log/biotoolssum/gunicorn_error.log
sudo chown $CURRENT_USER:$CURRENT_USER /var/log/biotoolssum/gunicorn_error.log
sudo touch /var/log/biotoolssum/celery.log
sudo chmod 755 /var/log/biotoolssum/celery.log
sudo chown $CURRENT_USER:$CURRENT_USER /var/log/biotoolssum/celery.log
sudo touch /var/log/biotoolssum/updatetools.log
sudo chmod 755 /var/log/biotoolssum/updatetools.log
sudo chown $CURRENT_USER:$CURRENT_USER /var/log/biotoolssum/updatetools.log

sudo touch /etc/logrotate.d/biotoolssum

cat << EOF | sudo tee /etc/logrotate.d/biotoolssum
/var/log/biotoolssum/gunicorn_error.log {
    rotate 12
    monthly
    compress
    missingok
    notifempty
    su $CURRENT_USER $CURRENT_USER
}

/var/log/biotoolssum/celery.log {
    rotate 12
    monthly
    compress
    missingok
    notifempty
    su $CURRENT_USER $CURRENT_USER
}

/var/log/biotoolssum/updatetools.log {
    rotate 12
    monthly
    compress
    missingok
    notifempty
    su $CURRENT_USER $CURRENT_USER
}
EOF

sudo logrotate -d /etc/logrotate.d/biotoolssum
sudo logrotate -f /etc/logrotate.d/biotoolssum

# SETTING UP MYSQL
sudo apt update
sudo apt install mysql-server

sudo mysql << EOF
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'password';
EOF

# SET THE PASSWORD TO password
sudo mysql_secure_installation

sudo mysql -u root -p << EOF
ALTER USER 'root'@'localhost' IDENTIFIED WITH auth_socket;
EOF

echo "ENTER A USERNAME FOR NEW MYSQL USER"
read username
echo "USERNAME_DB=$username" | sudo tee -a /home/$CURRENT_USER/biotoolssum-backend/.env
echo "ENTER A PASSWORD FOR NEW MYSQL USER"
read password
echo "PASSWORD_DB=$password" | sudo tee -a /home/$CURRENT_USER/biotoolssum-backend/.env

sudo mysql << EOF
CREATE USER '$username'@'localhost' IDENTIFIED BY '$password';
GRANT CREATE, ALTER, DROP, INSERT, UPDATE, INDEX, DELETE, SELECT, REFERENCES, RELOAD on *.* TO '$username'@'localhost' WITH GRANT OPTION;
FLUSH PRIVILEGES;
CREATE DATABASE biotoolssumDB;
EOF

# SETTING UP FLASKAPP SERVICE (GUNICORN)

sudo touch /etc/systemd/system/flaskapp.service

cat << EOF | sudo tee /etc/systemd/system/flaskapp.service
[Unit]
Description=Gunicorn instance to serve flaskapp
After=network.target
After=mysql.service

[Service]
User=$CURRENT_USER
Group=www-data
WorkingDirectory=/home/$CURRENT_USER/biotoolssum-backend
Environment="PATH=/home/$CURRENT_USER/biotoolssum-backend/venv/bin"
ExecStart=/home/$CURRENT_USER/biotoolssum-backend/venv/bin/gunicorn -c /home/$CURRENT_USER/biotoolssum-backend/gunicorn/gunicorn_conf.py wsgi:app

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl start flaskapp.service
sudo systemctl enable flaskapp.service

# SETTING UP RABBIT-MQ AND CELERY SERVICE

echo "ENTER A USERNAME FOR NEW RABBITMQ USER"
read username
echo "USERNAME_RABBIT=$username" | sudo tee -a /home/$CURRENT_USER/biotoolssum-backend/.env
echo "ENTER A PASSWORD FOR NEW RABBITMQ USER"
read password
echo "PASSWORD_RABBIT=$password" | sudo tee -a /home/$CURRENT_USER/biotoolssum-backend/.env
echo "ENTER A USERNAME FOR NEW RABBITMQ VHOST"
read vhost
echo "VHOST_RABBIT=$vhost" | sudo tee -a /home/$CURRENT_USER/biotoolssum-backend/.env

sudo apt-get install rabbitmq-server
sudo rabbitmqctl add_user $username $password
sudo rabbitmqctl add_vhost $vhost
sudo rabbitmqctl set_user_tags $username mytag
sudo rabbitmqctl set_permissions -p $vhost $username ".*" ".*" ".*"

sudo touch /etc/systemd/system/celery.service

cat << EOF | sudo tee /etc/systemd/system/celery.service
[Unit]
Description=Celery Service
After=network.target
After=mysql.service

[Service]
User=$CURRENT_USER
Group=www-data
WorkingDirectory=/home/$CURRENT_USER/biotoolssum-backend
Environment="PATH=/home/$CURRENT_USER/biotoolssum-backend/venv/bin"
ExecStart=/home/$CURRENT_USER/biotoolssum-backend/venv/bin/celery -A flaskapp.celery worker --logfile=/var/log/biotoolssum/celery.log --loglevel=INFO

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl start celery.service
sudo systemctl enable celery.service

# SETTING UP NGINX (server_name should be changed to a valid IP)

sudo apt update
sudo apt install nginx

sudo touch /etc/nginx/sites-available/flaskapp

cat << EOF | sudo tee /etc/nginx/sites-available/flaskapp
server {
    listen 80;
    server_name $ip www.$ip;
    location / {
	proxy_read_timeout 3600;
        include proxy_params;
        proxy_pass http://unix:/home/$CURRENT_USER/biotoolssum-backend/myproject.sock;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/flaskapp /etc/nginx/sites-enabled/flaskapp

sudo systemctl restart nginx

# SETTING UP A CRON JOB FOR UPDATING TOOLS

CURRENT_USER=$(whoami)
echo "MAILTO=\"\"" | sudo tee -a /tmp/cronjob
echo "0 0 */3 * * /home/$CURRENT_USER/biotoolssum-backend/venv/bin/python3 /home/$CURRENT_USER/biotoolssum-backend/updatetools.py >> /var/log/biotoolssum/updatetools.log 2>&1" | sudo tee -a /tmp/cronjob
cat /tmp/cronjob
crontab /tmp/cronjob
sudo rm /tmp/cronjob

sudo systemctl restart flaskapp.service
sudo systemctl restart celery.service

echo "REBOOT YOUR SYSTEM FOR NEW ENVIRONMENT VARIABLES TO WORK"

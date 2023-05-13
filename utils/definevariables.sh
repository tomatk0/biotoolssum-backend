#!/bin/bash

if ! grep -q "IP_ADDRESS=" /etc/environment; then
    echo "ENTER THE IP ADDRESS OF THIS VM (without http://)"
    read ip
    echo "IP_ADDRESS=\"$ip\"" | sudo tee -a /etc/environment
fi

if ! grep -q "GITHUB_TOKEN=" /etc/environment; then
    echo "ENTER A VALID GITHUB TOKEN"
    read token
    echo "GITHUB_TOKEN=\"$token\"" | sudo tee -a /etc/environment
fi

if ! grep -q "USERNAME_DB=" /etc/environment; then
    echo "ENTER A USERNAME FOR NEW MYSQL USER"
    read username
    echo "USERNAME_DB=\"$username\"" | sudo tee -a /etc/environment
fi

if ! grep -q "PASSWORD_DB=" /etc/environment; then
    echo "ENTER A PASSWORD FOR NEW MYSQL USER"
    read password
    echo "PASSWORD_DB=\"$password\"" | sudo tee -a /etc/environment
fi

if ! grep -q "USERNAME_RABBIT=" /etc/environment; then
    echo "ENTER A USERNAME FOR NEW RABBITMQ USER"
    read username
    echo "USERNAME_RABBIT=\"$username\"" | sudo tee -a /etc/environment
fi

if ! grep -q "PASSWORD_RABBIT=" /etc/environment; then
    echo "ENTER A PASSWORD FOR NEW RABBITMQ USER"
    read password
    echo "PASSWORD_RABBIT=\"$password\"" | sudo tee -a /etc/environment
fi

if ! grep -q "VHOST_RABBIT=" /etc/environment; then
    echo "ENTER A USERNAME FOR NEW RABBITMQ VHOST"
    read vhost
    echo "VHOST_RABBIT=\"$vhost\"" | sudo tee -a /etc/environment
fi

source /etc/environment

echo "REBOOT YOUR SYSTEM FOR NEW ENVIRONMENT VARIABLES TO WORK"
#!/bin/sh

echo "Please revise this file for MLTSHP deploys. Needs some work for the new environment."
exit 1

cp /home/ubuntu/rebuild/id_rsa /home/ubuntu/.ssh/
cp /home/ubuntu/rebuild/id_rsa.pub /home/ubuntu/.ssh/
chmod 0600 /home/ubuntu/.ssh/id_rsa
#sudo apt-get update
#sudo apt-get upgrade
#sudo reboot
sudo apt-get install python-pip
sudo pip install recaptcha-client==1.0.6
sudo pip install setuptools
sudo pip install tornado
sudo apt-get install supervisor
sudo apt-get install git-core
sudo apt-get install unzip
sudo chown ubuntu:ubuntu /srv/
cd /srv/
mkdir mltshp.com
cd mltshp.com
git clone git@github.com:mltshp/mltshp.git
mkdir logs
sudo apt-get install libmysqlclient-dev
sudo apt-get install mysql-server
sudo easy_install -U distribute
sudo apt-get install python-dev
sudo pip install mysql-python
sudo apt-get install libcurl4-openssl-dev 
sudo pip install pycurl
sudo pip install python-postmark
sudo pip install BeautifulSoup
sudo pip install tornadotoad
sudo apt-get install libjpeg-dev
sudo pip install PIL
sudo pip install celery
sudo pip install boto
sudo pip install tweepy
sudo apt-get install rabbitmq-server 
sudo rabbitmqctl delete_user guest
sudo rabbitmqctl add_user mltshp_user ----
sudo rabbitmqctl add_vhost localhost
sudo rabbitmqctl set_permissions -p localhost mltshp_user ".*" ".*" ".*"
cd ~/
mkdir sources
cd sources
#####
# EXPERIMENTAL
wget http://nginx.org/download/nginx-1.4.1.tar.gz -O nginx.tar.gz
tar -xzvf nginx.tar.gz
wget  --no-check-certificate https://github.com/vkholodkov/nginx-upload-module/archive/2.2.zip -O nginx-upload-module.zip
unzip nginx-upload-module.zip
wget --no-check-certificate https://github.com/gnosek/nginx-upstream-fair/tarball/master -O nginx-upstream-fair.tar.gz
tar -xzvf nginx-upstream-fair.tar.gz
sudo apt-get install libpcre3 libpcre3-dev
sudo apt-get install libssl-dev
cd nginx-1.4.1/
./configure --conf-path=/etc/nginx/nginx.conf --error-log-path=/var/log/nginx/error.log --pid-path=/var/run/nginx.pid --lock-path=/var/lock/nginx.lock --http-log-path=/var/log/nginx/access.log --http-client-body-temp-path=/var/lib/nginx/body --http-proxy-temp-path=/var/lib/nginx/proxy --http-fastcgi-temp-path=/var/lib/nginx/fastcgi --with-debug --with-http_stub_status_module  --with-http_ssl_module --with-http_gzip_static_module --with-http_realip_module  --with-ipv6 --add-module=/home/ubuntu/sources/gnosek-nginx-upstream-fair-a18b409/ --add-module=/home/ubuntu/sources/nginx-upload-module-2.2/
make
sudo apt-get install nginx
#####
#wget http://nginx.org/download/nginx-0.8.54.tar.gz -O nginx.tar.gz
#tar -xzvf nginx.tar.gz
#wget  --no-check-certificate https://github.com/vkholodkov/nginx-upload-module/tarball/2.2.0 -O nginx-upload-module.tar.gz
#tar -xzvf nginx-upload-module.tar.gz
#wget --no-check-certificate https://github.com/gnosek/nginx-upstream-fair/tarball/master -O nginx-upstream-fair.tar.gz
#tar -xzvf nginx-upstream-fair.tar.gz
#sudo apt-get install libpcre3 libpcre3-dev
#sudo apt-get install libssl-dev
#cd nginx-0.8.54
#./configure --conf-path=/etc/nginx/nginx.conf --error-log-path=/var/log/nginx/error.log --pid-path=/var/run/nginx.pid --lock-path=/var/lock/nginx.lock --http-log-path=/var/log/nginx/access.log --http-client-body-temp-path=/var/lib/nginx/body --http-proxy-temp-path=/var/lib/nginx/proxy --http-fastcgi-temp-path=/var/lib/nginx/fastcgi --with-debug --with-http_stub_status_module  --with-http_ssl_module --with-http_gzip_static_module --with-http_realip_module  --with-ipv6 --add-module=/home/ubuntu/sources/gnosek-nginx-upstream-fair-2131c73/ --add-module=/home/ubuntu/sources/vkholodkov-nginx-upload-module-2ec4e4f/
#make
# YOU WERE HERE
#sudo make install
sudo touch /var/log/nginx/error.log
sudo mkdir /var/lib/nginx
cd /etc/nginx/
sudo mv nginx.conf nginx.conf.backup
sudo ln -s /srv/mltshp.com/mltshp/setup/production.nginx.conf nginx.conf
sudo mkdir /etc/nginx/ssl
sudo cp /home/ubuntu/rebuild/server.crt /etc/nginx/ssl/
sudo cp /home/ubuntu/rebuild/server.key /etc/nginx/ssl/
sudo chmod 0600 /etc/nginx/ssl/server.*
cp /home/ubuntu/rebuild/celeryconfig.py /srv/mltshp.com/mltshp/
echo '********************* remember to set the IP address'
cd /tmp
sudo mkdir 1 2 3 4 5 6 7 8 9 0
cp /home/ubuntu/rebuild/settings.py /srv/mltshp.com/mltshp/
sudo cp /home/ubuntu/rebuild/supervisord.conf /etc/supervisor/conf.d/mltshp.conf
sudo /etc/init.d/supervisor start
sudo supervisorctl start all
#mysql -u root -p --execute "CREATE DATABASE mltshp"
